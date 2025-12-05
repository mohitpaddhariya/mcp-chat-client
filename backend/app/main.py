"""FastAPI main application with chat endpoints."""

import json
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from app.config import get_settings
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MCPInfo,
    MCPType,
)
from app.agent import MCPAgentBuilder, get_mcp_server_config
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting FastAPI + LangGraph Backend with MultiMCP")
    settings = get_settings()
    print(f"📦 Model: {settings.model_name}")
    print(f"🔌 Using langchain-mcp-adapters for MCP integration")
    print(f"🔌 MCP servers will be spawned as subprocesses (stdio transport)")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="LangGraph MCP Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and version."""
    return HealthResponse()


@app.get("/mcps", response_model=list[MCPInfo])
async def list_mcps():
    """List all available MCP servers."""
    mcps = []
    
    for mcp_type in MCPType:
        # Get MCP config
        config = get_mcp_server_config([mcp_type])
        
        mcp_info = MCPInfo(
            name=mcp_type.value,
            type=mcp_type,
            url=None,  # Using stdio, not HTTP
            available=False,
            tools=[]
        )
        
        # Try to connect and get tools
        try:
            client = MultiServerMCPClient(config)
            tools = await client.get_tools()
            mcp_info.tools = [tool.name for tool in tools]
            mcp_info.available = True
        except Exception as e:
            print(f"Failed to get tools for {mcp_type.value}: {e}")
            mcp_info.available = False
        
        mcps.append(mcp_info)
    
    return mcps


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI agent and get a response."""
    logger.info(f"[/chat] Received message: {request.message}")
    logger.info(f"[/chat] Selected MCPs: {request.selected_mcps}")
    
    settings = get_settings()
    
    # Build and run agent with MultiMCP
    agent_builder = MCPAgentBuilder(
        model_name=settings.model_name,
        google_api_key=settings.google_api_key
    )
    
    try:
        logger.info("[/chat] Running agent...")
        response, tools_used = await agent_builder.run_agent(
            user_message=request.message,
            selected_mcps=request.selected_mcps,
            conversation_history=request.conversation_history
        )
        
        logger.info(f"[/chat] Agent completed. Tools used: {tools_used}")
        return ChatResponse(
            response=response,
            tools_used=tools_used
        )
    
    except Exception as e:
        logger.error(f"[/chat] Agent execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream a chat response using Server-Sent Events (SSE)."""
    logger.info(f"[/chat/stream] Received message: {request.message}")
    logger.info(f"[/chat/stream] Selected MCPs: {request.selected_mcps}")
    
    settings = get_settings()
    
    # Build agent
    agent_builder = MCPAgentBuilder(
        model_name=settings.model_name,
        google_api_key=settings.google_api_key
    )
    
    async def event_generator():
        """Generate SSE events from agent stream."""
        try:
            logger.info("[/chat/stream] Starting stream...")
            async for event in agent_builder.stream_agent(
                user_message=request.message,
                selected_mcps=request.selected_mcps,
                conversation_history=request.conversation_history
            ):
                logger.info(f"[/chat/stream] Event: {event['type']}")
                yield {
                    "event": event["type"],
                    "data": json.dumps(event)
                }
            logger.info("[/chat/stream] Stream completed")
        except Exception as e:
            logger.error(f"[/chat/stream] Stream error: {str(e)}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"type": "error", "message": str(e)})
            }
    
    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
