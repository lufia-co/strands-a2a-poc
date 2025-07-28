import os
from dotenv import load_dotenv
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

CONNECTION_ID = os.getenv('NANGO_CONNECTION_ID')
SECRET_KEY = os.getenv('NANGO_SECRET_KEY')
if not CONNECTION_ID or not SECRET_KEY:
    raise ValueError("NANGO_CONNECTION_ID or NANGO_SECRET_KEY environment variable is not set.")


app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "")
    user_integration = payload.get("integration", None)

    mcp_client = MCPClient(lambda: streamablehttp_client(
        url="https://api.nango.dev/mcp",
        headers={
            "Authorization": f"Bearer {str(SECRET_KEY)}",
            "connection-id": str(CONNECTION_ID),
            "provider-config-key": user_integration
        }
    ))
    mcp_client.start()
    tools = mcp_client.list_tools_sync()

    agent = Agent(
        model="anthropic.claude-3-haiku-20240307-v1:0",
        system_prompt='''You are a helpful assistant that can interact with many third-party services via MCP client.
        You can use the tools provided by the MCP client to perform actions on behalf of the user. 
        Always ensure to use the correct integration context when making requests. the integration context is provided in the payload.
        If you need to use a tool, you can call it by its name and provide the necessary parameters.
        If you are unsure about how to use a tool, you can ask the user for clarification.''',
        tools=tools
    )

    return agent(user_message)

if __name__ == "__main__":
    app.run()
