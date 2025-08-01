import json
import os

from dotenv import load_dotenv
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands_tools.a2a_client import A2AClientToolProvider

load_dotenv()

model = BedrockModel(temperature=0)
provider = A2AClientToolProvider(known_agent_urls=["http://localhost:9000/"])

qna_agent = Agent(
    system_prompt='''
    You are a Q&A bot. 
    Answer questions based on the provided context and available tools. 
    You can rely on A2A Client tool provider that manages multiple A2A agents and exposes synchronous tools to find an agent that can retrieve information 
    necessary to answer the question.

    You just need to call the tool forwarding the user query to the agents available to you.
    ''',
    tools=provider.tools,
    record_direct_tool_call=False,
    model=model
)

user_query = f"""
When is my reading time?
the calendar id is {os.getenv("CALENDAR_ID")}
the timezone is Sao Paulo
"""

answer = qna_agent(user_query)

for trace in answer.metrics.traces:
    with open(f"logs/trace{trace.name}.json", "w") as f:
        f.write(json.dumps(trace.to_dict(), indent=2))