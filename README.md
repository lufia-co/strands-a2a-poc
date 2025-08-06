# Strands A2A Proof of Concept

A multi-agent system proof of concept built with Strands framework that demonstrates Agent-to-Agent (A2A) communication patterns. This project showcases how to build a distributed agent ecosystem where agents can communicate with each other to answer complex queries and perform tasks that require multiple specialized capabilities.

## Architecture Overview

The system consists of three main components:

1. **Multi-Agent Q&A API** (`multi_agent_strands.py`) - The main orchestrator service
2. **Google Calendar Agent** (`nango-caller-agent.py`) - A specialized agent for calendar operations
3. **Dynamic Agent Factory** (`dinamic_agent.py`) - A flexible agent creation and management system (work in progress)

## Features

- **Multi-Agent Orchestration**: Coordinate multiple specialized agents to handle complex queries
- **Agent-to-Agent Communication**: Direct communication between agents using A2A protocol
- **Google Calendar Integration**: Access and query Google Calendar data through Nango MCP client
- **Dynamic Agent Configuration**: Create and configure agents dynamically from database or configuration (work in progress)
- **Observability**: Built-in tracing and monitoring with Langfuse
- **RESTful API**: FastAPI-based HTTP endpoints for easy integration
- **Containerized Deployment**: Docker support for easy deployment

## Prerequisites

- Python 3.11+
- AWS Bedrock access (for LLM models)
- Nango account and API key (for Google Calendar integration)
- Langfuse account (for observability)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd strands-a2a-poc
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```bash
   NANGO_SECRET_KEY=your_nango_secret_key
   CALENDAR_AGENT_URL=http://localhost:8080
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_HOST=https://cloud.langfuse.com
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_DEFAULT_REGION=us-east-1
   ```

## Usage

### Running the System

1. **Start the Google Calendar Agent** (Terminal 1):
   ```bash
   python nango-caller-agent.py
   ```
   This starts the calendar agent on port 8080.

2. **Start the Main Q&A API** (Terminal 2):
   ```bash
   python multi_agent_strands.py
   ```
   This starts the main orchestrator API on port 8081.

### Making Requests

Send POST requests to the main API:

```bash
curl -X POST "http://localhost:8081/invocation" \
     -H "Content-Type: application/json" \
     -d '{"input": "When is my reading time? The calendar id is your_calendar_id and the timezone is Sao Paulo"}'
```

### Health Check

```bash
curl http://localhost:8081/
```

## API Documentation

### Endpoints

- `GET /` - Health check endpoint
- `POST /invocation` - Main query endpoint

### Request Format

```json
{
  "input": "Your question or command here"
}
```

### Response Format

```json
{
  "response": "Agent response or data",
  "status": "success"
}
```

## Agent Configuration

### Dynamic Agent Factory (Work in Progress)

The `dinamic_agent.py` module is under development and will provide a flexible system for creating and managing agents with different configurations. This feature is not yet ready for production use.

## Docker Deployment

### Build and Run the Calendar Agent

```bash
docker build -f dockerfile.nango -t calendar-agent .
docker run -p 8080:8080 --env-file .env calendar-agent
```

### Multi-Container Setup

For production deployment, consider using Docker Compose to orchestrate both services:

```yaml
version: '3.8'
services:
  calendar-agent:
    build:
      context: .
      dockerfile: dockerfile.nango
    ports:
      - "8080:8080"
    env_file:
      - .env
    
  qa-api:
    build: .
    ports:
      - "8081:8081"
    env_file:
      - .env
    depends_on:
      - calendar-agent
    environment:
      - CALENDAR_AGENT_URL=http://calendar-agent:8080
```

## Key Components

### A2AClientToolProvider

Provides tools for agent-to-agent communication:
- Discovers available agents through agent cards
- Routes messages to appropriate specialized agents
- Handles synchronous communication patterns

### A2AServer

Wraps Strands agents to make them compatible with A2A protocol:
- Exposes agents as A2A-compliant services
- Handles protocol translation
- Manages agent lifecycle and state

### MCP Integration

The system integrates with Model Context Protocol (MCP) for external service access:
- Google Calendar integration through Nango MCP client
- Extensible to other MCP-compatible services
- Secure authentication and connection management

## Observability

The system includes comprehensive observability features:

- **Langfuse Integration**: Automatic tracing of agent interactions
- **Request/Response Logging**: Detailed logs of all API calls
- **Error Tracking**: Structured error reporting and debugging
- **Performance Monitoring**: Latency and throughput metrics

## Troubleshooting

### Common Issues

1. **Agent Connection Errors**: Ensure all agents are running and accessible at configured URLs
2. **Authentication Failures**: Verify all API keys and credentials in `.env` file
3. **Model Access Issues**: Check AWS Bedrock permissions and region configuration
4. **Port Conflicts**: Ensure ports 8080 and 8081 are available