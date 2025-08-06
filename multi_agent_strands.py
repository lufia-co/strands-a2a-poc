import json
import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands_tools.a2a_client import A2AClientToolProvider
from langfuse import observe, get_client

load_dotenv() # init from env vars

# Initialize FastAPI app
app = FastAPI(
    title="Multi Agent Q&A API",
    description="A FastAPI service that provides Q&A capabilities using multi-agent system",
    version="1.0.0"
)

# Initialize Langfuse client
langfuse = get_client()


google_calendar_agent_url = os.getenv("CLOUD_RUN_CALENDAR_AGENT_URL")
if not google_calendar_agent_url:
    raise ValueError("CLOUD_RUN_CALENDAR_AGENT_URL environment variable is not set.")
provider = A2AClientToolProvider(known_agent_urls=[google_calendar_agent_url])

model = BedrockModel(temperature=0)

agent = Agent(
    system_prompt='''
    You are a Q&A bot. 
    Answer questions based on the provided context and available tools. 
    You can rely on A2A Client tool provider that manages multiple A2A agents and exposes synchronous tools to find an agent that can retrieve information 
    necessary to answer the question.

    You just need to call the tool forwarding the user input to the agents available to you.
    ''',
    tools=provider.tools,
    record_direct_tool_call=False,
    model=model
)

class InvocationRequest(BaseModel):
    input: str
    
class InvocationResponse(BaseModel):
    response: Any
    status: str = "success"

@observe(name="qna_agent_interaction")
def invoke_agent(user_input: str) -> Any:
    """
    Invoke the Q&A agent with the user input.
    """
    print(f"User Input: {user_input}")
    try:
        return agent(user_input)
    except Exception as e:
        print(f"Error invoking Q&A agent: {e}")
        return {"error": str(e)}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Multi Agent Q&A API is running"}

@app.post("/invocation", response_model=InvocationResponse)
async def invocation(request: InvocationRequest):
    try:
        with langfuse.start_as_current_span(name="agent-invocation") as trace:
            try:
                resp = invoke_agent(request.input)
                trace.update_trace(
                    output=json.dumps(resp) if resp else "No response",
                    tags=["multi-agent-invocation"]
                )
                return InvocationResponse(response=resp)
            except Exception as e:
                print(f"Error invoking Q&A agent: {e}")
                trace.update(level="ERROR")
                trace.update_trace(
                    output=json.dumps({"error": str(e)}),
                    tags=["multi-agent-invocation", "error"]
                )
                raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)