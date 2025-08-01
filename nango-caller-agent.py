import logging
import os
from dotenv import load_dotenv
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.multiagent.a2a import A2AServer
from mcp.client.streamable_http import streamablehttp_client
from strands.models.bedrock import BedrockModel
import uvicorn

logging.basicConfig(level=logging.INFO)

load_dotenv()

CONNECTION_ID = os.getenv('NANGO_CONNECTION_ID')
SECRET_KEY = os.getenv('NANGO_SECRET_KEY')

if not CONNECTION_ID or not SECRET_KEY:
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
    calendar_tools = mcp_client.list_tools_sync()
except Exception as e:
    raise RuntimeError(f"Failed to initialize MCP client: {e}")


model = BedrockModel(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    temperature=0
)
google_calendar_agent = Agent(
    model=model,
    name="google-calendar-agent",
    agent_id="google-calendar-agent",
    description="Google Calendar Agent",
    system_prompt='''You are a connection agent that interacts with google-calendar via MCP client.
    Use only the provided tools to retrieve information relation to user's google calendar. 
    If none of the tools can help you, inform the user that you can not help with that.
    
    Important:
    1. the default location for timezone is Sao Paulo, Brazil.
    1.1. If the user does not specify a timezone, you can assume it's Sao Paulo.
    2. If any exception happens, just inform the user you're not being able to retrieve data due to internal problems.
    3. You can use current_time tool to clarify and define which day is today.

    Always answer with a JSON object
    DO NOT use emojis in the answers
    ''',
    record_direct_tool_call=False,
    tools=calendar_tools,
)

server = A2AServer(agent=google_calendar_agent)
fastapi_app = server.to_fastapi_app()

uvicorn.run(fastapi_app, host="0.0.0.0", port=9000)

