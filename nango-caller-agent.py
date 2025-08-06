def patch_strands_a2a_executor():
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

patch_strands_a2a_executor()

import os
import uvicorn

from dotenv import load_dotenv
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands.multiagent.a2a import A2AServer
from mcp.client.streamable_http import streamablehttp_client
from strands.models.bedrock import BedrockModel

print("Loading environment variables...")
load_dotenv()

print("Setting up MCP client...")
CONNECTION_ID = os.getenv('NANGO_CONNECTION_ID')
SECRET_KEY = os.getenv('NANGO_SECRET_KEY')

if not CONNECTION_ID or not SECRET_KEY:
    print("Error: NANGO_CONNECTION_ID or NANGO_SECRET_KEY environment variable is not set.")
    raise ValueError("NANGO_CONNECTION_ID or NANGO_SECRET_KEY environment variable is not set.")

@tool
def nango_mcp_calendar_tools(connection_id: str):
    mcp_client = MCPClient(lambda: streamablehttp_client(
        url="https://api.nango.dev/mcp",
        headers={
            "Authorization": f"Bearer {str(SECRET_KEY)}",
            "connection-id": connection_id,
            "provider-config-key": "google-calendar"
        }
    ))
    mcp_client.start()
    print("MCP client started successfully.")
    return mcp_client.list_tools_sync()

print("Creating Google Calendar Agent...")
google_calendar_agent = Agent(
    model=BedrockModel(model_id="anthropic.claude-3-haiku-20240307-v1:0", temperature=0),
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
    tools=[nango_mcp_calendar_tools],
)

print("Creating A2A Server...")
server = A2AServer(agent=google_calendar_agent, serve_at_root=True, http_url="https://nango-caller-agent-931384239836.us-east1.run.app")

print("Converting A2A Server to FastAPI app...")
fastapi_app = server.to_fastapi_app()

uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)