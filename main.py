from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
 
@app.entrypoint
def invoke(payload):
    """
    This function is the entry point for the Bedrock Agent Core application.
    It processes the incoming payload and returns it.
    """

    user_message = payload.get("prompt", "Hello, world!")
    return { "response": f"Processed message: {user_message}" }

if __name__ == "__main__":
    app.run()
 