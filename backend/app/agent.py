"""LangGraph agent with MultiMCP support using langchain-mcp-adapters."""

import json
import logging
from typing import Any, AsyncGenerator

# Configure logging
logger = logging.getLogger(__name__)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from app.schemas import ChatMessage, MCPType


def get_mcp_server_config(
    selected_mcps: list[MCPType],
    filesystem_path: str = "/Users/mohitpaddhariya"
) -> dict[str, dict]:
    """
    Build MCP server configuration for selected MCPs.
    
    Uses stdio transport - MCP servers run as subprocesses.
    
    Available MCP Servers:
    - filesystem: Local filesystem operations (read, write, list files)
    """
    logger.info(f"[get_mcp_server_config] Building config for: {selected_mcps}")
    config = {}
    
    for mcp_type in selected_mcps:
        if mcp_type == MCPType.FILESYSTEM:
            # Filesystem MCP - runs via npx as subprocess
            config["filesystem"] = {
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    filesystem_path  # Allowed directory
                ],
                "transport": "stdio",
            }
    
    return config


class MCPAgentBuilder:
    """Builds LangGraph agents with MultiMCP support."""
    
    def __init__(self, model_name: str, google_api_key: str):
        """Initialize the agent builder."""
        logger.info(f"[MCPAgentBuilder] Initializing with model: {model_name}")
        self.model_name = model_name
        self.google_api_key = google_api_key
        
        # Create the LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.google_api_key,
            temperature=0.7,
        )
        logger.info("[MCPAgentBuilder] LLM initialized")
    
    def _build_messages(
        self, 
        user_message: str, 
        conversation_history: list[ChatMessage] | None
    ) -> list[BaseMessage]:
        """Build message list from conversation history."""
        messages = []
        
        if conversation_history:
            for msg in conversation_history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
        
        messages.append(HumanMessage(content=user_message))
        return messages
    
    def _get_system_prompt(self, selected_mcps: list[MCPType], available_tools: list[str] | None = None) -> str:
        """Get system prompt based on available tools."""
        if selected_mcps and available_tools:
            tools_info = ", ".join(available_tools) if available_tools else "none"
            mcps_info = ", ".join([mcp.value for mcp in selected_mcps])
            return (
                f"You currently have access to the following MCP servers: {mcps_info}. "
                f"Available tools: {tools_info}. "
                "IMPORTANT: Ignore any previous messages in the conversation history that say you don't have access to tools - "
                "your tool access has been updated for this request. You DO have tools available now. "
                "You can access the user's local files under /Users/mohitpaddhariya using filesystem tools (e.g., read_file, list_directory). "
                "Do not say you cannot access local files; instead, invoke the appropriate tool. "
                "Use the tools available to you to help the user with their request."
            )
        else:
            return (
                "You currently do not have access to any external tools or MCP servers. "
                "If the user asks you to perform actions that require tools (like reading files, listing directories, etc.), "
                "politely explain that no tools are currently selected and suggest they select the appropriate MCP tools from the sidebar."
            )
    
    async def run_agent(
        self,
        user_message: str,
        selected_mcps: list[MCPType],
        conversation_history: list[ChatMessage] | None = None
    ) -> tuple[str, list[str]]:
        """
        Run the agent with selected MCP servers.
        
        Uses MultiServerMCPClient to connect to multiple MCP servers via stdio.
        """
        logger.info(f"[run_agent] Starting with message: {user_message[:50]}...")
        logger.info(f"[run_agent] Selected MCPs: {selected_mcps}")
        tools_used = []
        
        # Build MCP config for selected servers
        mcp_config = get_mcp_server_config(selected_mcps)
        logger.info(f"[run_agent] MCP config: {mcp_config}")
        
        if not mcp_config:
            # No MCPs selected - run without tools
            logger.info("[run_agent] No MCPs - running without tools")
            system_prompt = self._get_system_prompt([], None)
            messages = [SystemMessage(content=system_prompt)] + self._build_messages(user_message, conversation_history)
            response = await self.llm.ainvoke(messages)
            logger.info(f"[run_agent] Response received: {response.content[:50]}...")
            return response.content, []
        
        # Use MultiServerMCPClient (creates new session per tool invocation)
        logger.info("[run_agent] Creating MultiServerMCPClient...")
        client = MultiServerMCPClient(mcp_config)
        
        # Get all tools from connected MCP servers
        logger.info("[run_agent] Getting tools from MCP servers...")
        tools = await client.get_tools()
        
        # Enable error handling for all tools
        for tool in tools:
            tool.handle_tool_error = True
        
        tool_names = [tool.name for tool in tools]
        logger.info(f"[run_agent] Loaded {len(tools)} tools from MCP servers:")
        for tool in tools:
            logger.info(f"   - {tool.name}")
        
        # Create ReAct agent with MCP tools
        logger.info("[run_agent] Creating ReAct agent...")
        agent = create_react_agent(
            model=self.llm,
            tools=tools,
        )
        
        # Build messages with system prompt prepended
        system_prompt = self._get_system_prompt(selected_mcps, tool_names)
        messages = [SystemMessage(content=system_prompt)] + self._build_messages(user_message, conversation_history)
        
        # Run the agent
        logger.info("[run_agent] Invoking agent...")
        result = await agent.ainvoke({"messages": messages})
        logger.info("[run_agent] Agent invocation complete")
        
        # Extract response and tools used
        final_messages = result.get("messages", [])
        
        # Find tools that were called
        for msg in final_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tools_used.append(tool_call["name"])
        
        # Get final response
        last_message = final_messages[-1] if final_messages else None
        response_content = last_message.content if last_message else "No response generated."
        
        logger.info(f"[run_agent] Tools used: {tools_used}")
        logger.info(f"[run_agent] Response: {response_content[:100]}...")
        
        return response_content, tools_used
    
    async def stream_agent(
        self,
        user_message: str,
        selected_mcps: list[MCPType],
        conversation_history: list[ChatMessage] | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream the agent's response with MCP tools.
        """
        logger.info(f"[stream_agent] Starting with message: {user_message[:50]}...")
        logger.info(f"[stream_agent] Selected MCPs: {selected_mcps}")
        
        # Build MCP config for selected servers
        mcp_config = get_mcp_server_config(selected_mcps)
        logger.info(f"[stream_agent] MCP config: {mcp_config}")
        
        if not mcp_config:
            # No MCPs selected - stream without tools
            logger.info("[stream_agent] No MCPs - streaming without tools")
            system_prompt = self._get_system_prompt([], None)
            messages = [SystemMessage(content=system_prompt)] + self._build_messages(user_message, conversation_history)
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield {"type": "token", "content": chunk.content}
            logger.info("[stream_agent] Stream complete (no tools)")
            yield {"type": "done", "tools_used": []}
            return
        
        tools_used = []
        
        # Use MultiServerMCPClient (creates new session per tool invocation)
        logger.info("[stream_agent] Creating MultiServerMCPClient...")
        client = MultiServerMCPClient(mcp_config)
        logger.info("[stream_agent] Getting tools...")
        tools = await client.get_tools()

        # Enable error handling for all tools
        for tool in tools:
            tool.handle_tool_error = True

        tool_names = [tool.name for tool in tools]
        logger.info(f"[stream_agent] Loaded {len(tools)} tools")
        
        # Create ReAct agent
        logger.info("[stream_agent] Creating ReAct agent...")
        agent = create_react_agent(
            model=self.llm,
            tools=tools,
        )
        
        # Build messages with system prompt prepended
        system_prompt = self._get_system_prompt(selected_mcps, tool_names)
        messages = [SystemMessage(content=system_prompt)] + self._build_messages(user_message, conversation_history)
        
        # Stream agent execution
        logger.info("[stream_agent] Starting agent stream...")
        async for event in agent.astream_events(
            {"messages": messages},
            version="v2"
        ):
            kind = event["event"]
            logger.debug(f"[stream_agent] Event: {kind}")
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield {"type": "token", "content": content}
            
            elif kind == "on_tool_start":
                tool_name = event["name"]
                tools_used.append(tool_name)
                # Convert input to string to avoid serialization issues
                tool_input = event["data"].get("input", {})
                try:
                    # Try to serialize, if fails convert to string
                    json.dumps(tool_input)
                except (TypeError, ValueError):
                    tool_input = str(tool_input)
                yield {
                    "type": "tool_start",
                    "tool": tool_name,
                    "input": tool_input
                }
            
            elif kind == "on_tool_end":
                logger.info(f"[stream_agent] Tool ended: {event['name']}")
                yield {
                    "type": "tool_end",
                    "tool": event["name"],
                    "output": str(event["data"].get("output", ""))[:500]
                }
        
        logger.info(f"[stream_agent] Stream complete. Tools used: {tools_used}")
        yield {"type": "done", "tools_used": tools_used}
