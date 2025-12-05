# FastAPI + LangGraph Backend with MCP Integration

A Python backend that dynamically builds AI agents with MCP (Model Context Protocol) tool integration.

## Architecture

```
┌──────────────────────────────┐
│        Next.js Frontend      │
│                              │
│  • Chat UI                   │
│  • MCP selection (checkbox)  │
│  • Streaming responses       │
│                              │
└───────────────┬──────────────┘
                │ HTTP / SSE
                ▼
┌──────────────────────────────┐
│        Python Backend        │
│   (FastAPI + LangGraph)      │
│                              │
│  • Receives chat request     │
│  • Loads selected MCPs       │
│  • Builds agent dynamically  │
│  • Executes tools            │
│  • Streams response          │
│                              │
└───────────────┬──────────────┘
                │ HTTP MCP
                ▼
┌──────────────────────────────┐
│         MCP Servers          │
│                              │
│  • Filesystem MCP            │
│  • AWS S3 MCP                │
│  • AWS API MCP               │
│                              │
└──────────────────────────────┘
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application with endpoints
│   ├── config.py        # Configuration and settings
│   ├── schemas.py       # Pydantic models for requests/responses
│   ├── mcp_client.py    # MCP server client implementation
│   └── agent.py         # LangGraph agent builder
├── .env.example         # Environment variables template
├── pyproject.toml       # Project dependencies
└── README.md
```

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and MCP server URLs
   ```

3. **Run the server:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## API Endpoints

### Health Check
```
GET /health
```

### List Available MCPs
```
GET /mcps
```
Returns list of configured MCP servers and their available tools.

### Chat (Non-streaming)
```
POST /chat
```
Request body:
```json
{
  "message": "Your message here",
  "selected_mcps": ["filesystem", "s3"],
  "conversation_history": []
}
```

### Chat (Streaming)
```
POST /chat/stream
```
Returns Server-Sent Events (SSE) with tokens and tool execution events.

## MCP Server Integration

The backend connects to MCP servers via HTTP. Configure the URLs in `.env`:

- `MCP_FILESYSTEM_URL` - Filesystem operations MCP
- `MCP_S3_URL` - AWS S3 operations MCP  
- `MCP_AWS_API_URL` - AWS API operations MCP

## How It Works

1. **Request received** - Frontend sends chat message with selected MCPs
2. **MCP initialization** - Backend connects to selected MCP servers and fetches available tools
3. **Agent building** - LangGraph agent is dynamically built with MCP tools bound to the LLM
4. **Execution** - Agent processes the message, calling MCP tools as needed
5. **Response** - Final response is streamed back to the frontend