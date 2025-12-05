"use client";

import { useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { ChatMessage } from "../types";
import { MCPSelector } from "./mcp-selector";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";
import { Bot } from "lucide-react";

export function ChatInterface() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [selectedMCPs, setSelectedMCPs] = useState<string[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState("");
    const [streamingTools, setStreamingTools] = useState<
        { tool: string; input?: any; output?: any }[]
    >([]);

    const hasStarted = messages.length > 0 || isStreaming;

    const handleToggleMCP = (mcpType: string) => {
        setSelectedMCPs((prev) =>
            prev.includes(mcpType)
                ? prev.filter((t) => t !== mcpType)
                : [...prev, mcpType]
        );
    };

    const handleSend = async (text: string) => {
        const userMsg: ChatMessage = { role: "user", content: text };
        setMessages((prev) => [...prev, userMsg]);

        setIsStreaming(true);
        setStreamingContent("");
        setStreamingTools([]);

        let currentContent = "";
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let currentTools: { tool: string; input?: any; output?: any }[] = [];

        try {
            await fetchEventSource("http://127.0.0.1:8000/chat/stream", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: text,
                    selected_mcps: selectedMCPs,
                    conversation_history: messages,
                }),
                onopen: async (res) => {
                    if (res.ok && res.status === 200) {
                        return;
                    } else if (res.status >= 400 && res.status < 500 && res.status !== 429) {
                        throw new Error("Client side error " + res.status);
                    }
                },
                onmessage(msg) {
                    if (msg.event === "token") {
                        const data = JSON.parse(msg.data);
                        currentContent += data.content;
                        setStreamingContent(currentContent);
                    } else if (msg.event === "tool_start") {
                        const data = JSON.parse(msg.data);
                        const newTool = { tool: data.tool, input: data.input };
                        currentTools = [...currentTools, newTool];
                        setStreamingTools(currentTools);
                    } else if (msg.event === "tool_end") {
                        // Optional: update tool output
                    } else if (msg.event === "done") {
                        // Stream finished
                    } else if (msg.event === "error") {
                        throw new Error("Stream error");
                    }
                },
                onclose() {
                    setIsStreaming(false);
                    setMessages((prev) => [
                        ...prev,
                        { role: "assistant", content: currentContent },
                    ]);
                },
                onerror(err) {
                    console.error("EventSource error:", err);
                    setIsStreaming(false);
                    throw err;
                },
            });
        } catch (err) {
            console.error("Failed to stream response", err);
            setIsStreaming(false);
        }
    };

    return (
        <div className="flex w-full h-screen max-h-screen bg-black text-foreground overflow-hidden font-sans p-4 gap-4">
            {/* Background Gradients (Subtle & Deep) */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
                <div className="absolute top-[-20%] left-[5%] w-[600px] h-[600px] bg-blue-900/10 rounded-full blur-[120px] mix-blend-screen" />
                <div className="absolute bottom-[-10%] right-[10%] w-[500px] h-[500px] bg-purple-900/10 rounded-full blur-[100px] mix-blend-screen" />
            </div>

            {/* Left Sidebar: MCP List */}
            <aside className="hidden md:flex flex-col w-64 z-10 gap-4">
                <div className="flex items-center gap-2 px-2 py-4">
                    <div className="w-8 h-8 rounded-full bg-zinc-900/80 border border-zinc-800 flex items-center justify-center shadow-lg shadow-black/20">
                        <div className="w-4 h-4 text-xs font-bold text-center text-zinc-400 flex items-center justify-center">MCP</div>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    <div className="glass-panel rounded-2xl p-4 h-full border-zinc-800/50 bg-zinc-900/40">
                        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4 px-2">Tools</h3>
                        <MCPSelector selectedMCPs={selectedMCPs} onToggleMCP={handleToggleMCP} />
                    </div>
                </div>
            </aside>

            {/* Main Content: Chat Card */}
            <main className="flex-1 flex flex-col relative z-20 min-w-0">
                <div className="flex-1 relative flex flex-col w-full h-full glass-panel rounded-3xl shadow-2xl shadow-black/50 overflow-hidden border border-white/5">

                    {/* Header (Mobile only) */}
                    <header className="flex-none md:hidden p-4 border-b border-zinc-800 bg-black/80 backdrop-blur-md flex items-center justify-between">
                        <span className="font-bold text-lg text-white">Chat</span>
                    </header>

                    {/* Content Area */}
                    {hasStarted ? (
                        /* Chat View */
                        <div className="flex-1 flex flex-col min-h-0 bg-transparent">
                            <MessageList
                                messages={messages}
                                streamingContent={streamingContent}
                                streamingTools={streamingTools}
                                isStreaming={isStreaming}
                            />
                            <div className="flex-none p-4 pb-6 w-full max-w-3xl mx-auto">
                                <MessageInput onSend={handleSend} disabled={isStreaming} />
                            </div>
                        </div>
                    ) : (
                        /* Hero View */
                        <div className="flex-1 flex flex-col items-center justify-center p-4 bg-transparent">
                            <span className="text-sm font-medium text-zinc-600 mb-8 opacity-50 tracking-widest uppercase">✦ chat-mcp</span>
                            <div className="w-full max-w-xl flex flex-col items-center gap-8 -mt-10">
                                <div className="space-y-4 text-center">
                                    {/* Center Image/Card Group from reference (Mock representation) */}
                                </div>

                                <div className="w-full">
                                    <MessageInput onSend={handleSend} disabled={isStreaming} />
                                </div>
                                <div className="text-sm text-zinc-600">
                                    Ask anything...
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>



        </div>
    );
}
