"""Pydantic schemas for request/response models."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class MCPType(str, Enum):
    """
    Available MCP (Model Context Protocol) server types.
    
    Select the filesystem MCP to enable file operations:
    - filesystem: File operations (read, write, list, search files)
    """
    FILESYSTEM = "filesystem"


class ChatMessage(BaseModel):
    """
    A single message in the conversation history.
    
    Used to maintain context across multiple chat turns.
    """
    role: str = Field(
        ..., 
        description="Role of the message sender. Must be 'user' or 'assistant'",
        json_schema_extra={"examples": ["user", "assistant"]}
    )
    content: str = Field(
        ..., 
        description="The text content of the message",
        json_schema_extra={"examples": ["Hello, how can you help me?", "I can help you with file operations!"]}
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"role": "user", "content": "List all Python files in my project"},
                {"role": "assistant", "content": "I found 5 Python files in your project..."}
            ]
        }
    }


class ChatRequest(BaseModel):
    """
    Request body for the chat endpoint.
    
    Send a message to the AI agent with optional MCP tool selection
    and conversation history for context.
    """
    message: str = Field(
        ..., 
        description="The user's message or question to the AI agent",
        min_length=1,
        max_length=10000,
        json_schema_extra={"examples": ["List the files in my home directory", "Read the content of README.md"]}
    )
    selected_mcps: list[MCPType] = Field(
        default_factory=list,
        description="List of MCP servers to enable for this request. Leave empty for chat without tools.",
        json_schema_extra={"examples": [["filesystem"], ["filesystem", "s3"], []]}
    )
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages in the conversation for context. Most recent messages should be at the end."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "What is 2 + 2?",
                    "selected_mcps": [],
                    "conversation_history": []
                },
                {
                    "message": "List the files in /Users/mohit/projects",
                    "selected_mcps": ["filesystem"],
                    "conversation_history": []
                },
                {
                    "message": "Now read the README.md file",
                    "selected_mcps": ["filesystem"],
                    "conversation_history": [
                        {"role": "user", "content": "List the files in /Users/mohit/projects"},
                        {"role": "assistant", "content": "Found: README.md, main.py, requirements.txt"}
                    ]
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """
    Response from the chat endpoint.
    
    Contains the AI agent's response and a list of tools that were used.
    """
    response: str = Field(
        ..., 
        description="The AI agent's response to the user's message"
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="List of MCP tool names that were invoked during this request",
        json_schema_extra={"examples": [[], ["list_directory"], ["read_file", "write_file"]]}
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "response": "2 + 2 = 4",
                    "tools_used": []
                },
                {
                    "response": "The directory contains: main.py, README.md, requirements.txt",
                    "tools_used": ["list_directory"]
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """
    Health check response indicating the API status.
    """
    status: str = Field(
        default="ok", 
        description="Current health status of the API",
        json_schema_extra={"examples": ["ok", "degraded"]}
    )
    version: str = Field(
        default="0.1.0", 
        description="Current API version"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"status": "ok", "version": "0.1.0"}
            ]
        }
    }


class MCPInfo(BaseModel):
    """
    Information about an available MCP server.
    
    Describes an MCP server that can be selected for tool capabilities.
    """
    name: str = Field(
        ..., 
        description="Display name of the MCP server",
        json_schema_extra={"examples": ["filesystem", "s3"]}
    )
    type: MCPType = Field(
        ..., 
        description="The MCP type identifier to use in requests"
    )
    url: Optional[str] = Field(
        default=None, 
        description="Server URL (null for stdio-based servers)"
    )
    available: bool = Field(
        default=False, 
        description="Whether this MCP server is currently available"
    )
    tools: list[str] = Field(
        default_factory=list,
        description="List of tool names provided by this MCP server (populated when connected)",
        json_schema_extra={"examples": [["read_file", "write_file", "list_directory"]]}
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "filesystem",
                    "type": "filesystem",
                    "url": None,
                    "available": True,
                    "tools": ["read_file", "write_file", "list_directory", "search_files"]
                }
            ]
        }
    }


# Streaming event models for documentation
class StreamTokenEvent(BaseModel):
    """SSE event containing a token from the AI response stream."""
    type: str = Field(default="token", description="Event type identifier")
    content: str = Field(..., description="The token content being streamed")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{"type": "token", "content": "Hello"}]
        }
    }


class StreamToolStartEvent(BaseModel):
    """SSE event indicating a tool execution has started."""
    type: str = Field(default="tool_start", description="Event type identifier")
    tool: str = Field(..., description="Name of the tool being executed")
    input: dict = Field(default_factory=dict, description="Input arguments passed to the tool")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{"type": "tool_start", "tool": "list_directory", "input": {"path": "/Users/mohit"}}]
        }
    }


class StreamToolEndEvent(BaseModel):
    """SSE event indicating a tool execution has completed."""
    type: str = Field(default="tool_end", description="Event type identifier")
    tool: str = Field(..., description="Name of the tool that completed")
    output: str = Field(..., description="Output/result from the tool execution")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{"type": "tool_end", "tool": "list_directory", "output": "[\"file1.txt\", \"file2.py\"]"}]
        }
    }


class StreamDoneEvent(BaseModel):
    """SSE event indicating the stream has completed."""
    type: str = Field(default="done", description="Event type identifier")
    tools_used: list[str] = Field(default_factory=list, description="List of all tools used during this request")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{"type": "done", "tools_used": ["list_directory", "read_file"]}]
        }
    }


class StreamErrorEvent(BaseModel):
    """SSE event indicating an error occurred."""
    type: str = Field(default="error", description="Event type identifier")
    message: str = Field(..., description="Error message describing what went wrong")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{"type": "error", "message": "Failed to connect to MCP server"}]
        }
    }
