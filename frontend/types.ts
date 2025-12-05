export interface MCPInfo {
  name: string;
  type: string;
  url: string | null;
  available: boolean;
  tools: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  selected_mcps: string[];
  conversation_history?: ChatMessage[];
}

export interface ChatResponse {
  response: string;
  tools_used: string[];
}

export interface StreamEvent {
  type: "token" | "tool_start" | "tool_end" | "done" | "error";
  content?: string;
  tool?: string;
  input?: any;
  output?: any;
  tools_used?: string[];
}
