# This runtime patch is needed as workaround until is fixed by -> https://github.com/strands-agents/sdk-python/issues/589
# ------- # ------- # ------- # ------- # ------- 
from strands.multiagent.a2a.executor import StrandsA2AExecutor
from a2a.server.tasks import TaskUpdater

# Patch the execute method to fix the contextId/context_id issue
original_execute = StrandsA2AExecutor.execute

async def patched_execute(self, context, event_queue):
    """Patched execute method that fixes the contextId attribute error."""
    task = context.current_task
    if not task:
        from a2a.utils import new_task
        task = new_task(context.message)
        await event_queue.enqueue_event(task)

    # Fix: use context_id instead of contextId
    updater = TaskUpdater(event_queue, task.id, task.context_id)

    try:
        await self._execute_streaming(context, updater)
    except Exception as e:
        from a2a.types import InternalError
        from a2a.utils.errors import ServerError
        raise ServerError(error=InternalError()) from e

# Apply the patch
StrandsA2AExecutor.execute = patched_execute
# ------- # ------- # ------- # ------- # ------- 

import os

from dotenv import load_dotenv
from langfuse import get_client, observe
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.multiagent.a2a import A2AServer
from mcp.client.streamable_http import streamablehttp_client
from strands.models.bedrock import BedrockModel
from mangum import Mangum   # <-- Lambda adapter

print("Loading environment variables...")
load_dotenv()

print("Initializing Langfuse client...")
langfuse = get_client() # it will automatically read from environment variables

customer = "test_customer" #for testing TAGs on langfuse traces

print("Setting up MCP client...")
CONNECTION_ID = os.getenv('NANGO_CONNECTION_ID')
SECRET_KEY = os.getenv('NANGO_SECRET_KEY')

if not CONNECTION_ID or not SECRET_KEY:
    print("Error: NANGO_CONNECTION_ID or NANGO_SECRET_KEY environment variable is not set.")
    raise ValueError("NANGO_CONNECTION_ID or NANGO_SECRET_KEY environment variable is not set.")

mcp_client = MCPClient(lambda: streamablehttp_client(
    url="https://api.nango.dev/mcp",
    headers={
        "Authorization": f"Bearer {str(SECRET_KEY)}",
        "connection-id": str(CONNECTION_ID),
        "provider-config-key": "google-calendar"
    }
))

try:
    mcp_client.start()
    print("MCP client started successfully.")
    calendar_tools = mcp_client.list_tools_sync()
except Exception as e:
    print(f"Error initializing MCP client: {e}")
    raise RuntimeError(f"Failed to initialize MCP client: {e}")


print("Setting up Bedrock model...")
model = BedrockModel(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    temperature=0
)

print("Creating Google Calendar Agent...")
google_calendar_agent = Agent(
    model=model,
    name="google-calendar-agent",
    agent_id="google-calendar-agent",
    description="Google Calendar Agent",
    system_prompt='''You are a connection agent that interacts with google-calendar via MCP client.
    Use only the provided tools to retrieve information related to the user's google calendar. 
    If none of the tools can help you, inform the user that you cannot help with that.
    
    Important:
    1. The default location for timezone is Sao Paulo, Brazil.
    1.1. If the user does not specify a timezone, you can assume it's Sao Paulo.
    2. If any exception happens, just inform the user you're not being able to retrieve data due to internal problems.
    3. You can use current_time tool to clarify and define which day is today.

    Always answer with a JSON object
    DO NOT use emojis in the answers
    ''',
    record_direct_tool_call=False,
    tools=calendar_tools,
)

print("Creating A2A Server...")
server = A2AServer(agent=google_calendar_agent, serve_at_root=True)

print("Converting A2A Server to FastAPI app...")
fastapi_app = server.to_fastapi_app()
print("Wrapping FastAPI app with Mangum for AWS Lambda compatibility...")
base_handler = Mangum(fastapi_app)


@observe(name="google-calendar-agent")
def handler(event, context):
    print("Handler invoked with event:", event)
    trace = None
    try:
        with langfuse.start_as_current_span(name="google-calendar-agent-invocation") as trace:
            trace.update_trace(
                input={"event": event, "lambda_context": str(context)},
                tags=[f"customer:{customer}", f"agent:{google_calendar_agent.agent_id}"]
            )
            
            response = base_handler(event, context)
            
            trace.update_trace(
                output={"response": response},
                tags=[f"customer:{customer}", f"agent:{google_calendar_agent.agent_id}", "status:success"]
            )
            
            return response
        
    except Exception as e:
        if trace:
            trace.update(level="ERROR")
            trace.update_trace(
                output={"error": str(e), "error_type": type(e).__name__},
                tags=[f"customer:{customer}", f"agent:{google_calendar_agent.agent_id}", "status:error"],
            )
        raise
