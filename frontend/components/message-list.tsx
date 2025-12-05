"use client";

import { ChatMessage } from "../types";
import ReactMarkdown from "react-markdown";
import { Bot, User, Terminal, CheckCircle2, Loader2 } from "lucide-react";
import { twMerge } from "tailwind-merge";
import { motion } from "framer-motion";

interface MessageListProps {
    messages: ChatMessage[];
    streamingContent: string;
    streamingTools: { tool: string; input?: any; output?: any }[];
    isStreaming: boolean;
}

export function MessageList({
    messages,
    streamingContent,
    streamingTools,
    isStreaming,
}: MessageListProps) {
    return (
        <div className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
            {messages.map((msg, idx) => (
                <MessageItem key={idx} role={msg.role} content={msg.content} />
            ))}

            {isStreaming && (
                <div className="space-y-4">
                    {/* Render completed tools during stream */}
                    {streamingTools.map((tool, idx) => (
                        <ToolExecution key={idx} tool={tool.tool} input={tool.input} />
                    ))}

                    {/* Render streaming content */}
                    {streamingContent && (
                        <MessageItem role="assistant" content={streamingContent} isStreaming />
                    )}

                    {/* Loading indicator if no content yet */}
                    {!streamingContent && streamingTools.length === 0 && (
                        <div className="flex items-center gap-2 text-zinc-400 text-sm pl-12 animate-pulse">
                            <Loader2 size={14} className="animate-spin" />
                            Thinking...
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function MessageItem({
    role,
    content,
    isStreaming,
}: {
    role: "user" | "assistant";
    content: string;
    isStreaming?: boolean;
}) {
    const isUser = role === "user";

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={twMerge(
                "flex gap-4 max-w-4xl mx-auto px-4",
                isUser ? "justify-end" : "justify-start"
            )}
        >
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-zinc-800/50 text-zinc-400 flex items-center justify-center shrink-0 mt-1 shadow-inner ring-1 ring-white/5">
                    <Bot size={16} />
                </div>
            )}

            <div
                className={twMerge(
                    "relative max-w-[85%] rounded-2xl p-4 text-base leading-relaxed shadow-sm",
                    isUser
                        ? "bg-zinc-800 text-zinc-100 border border-white/5 shadow-md shadow-black/20"
                        : "bg-transparent text-zinc-300 px-0"
                )}
            >
                <div className={twMerge("prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 prose-code:text-blue-400")}>
                    <ReactMarkdown>{content}</ReactMarkdown>
                </div>
                {isStreaming && (
                    <span className="inline-block w-2 h-5 ml-1 align-middle bg-blue-500 animate-pulse rounded-sm" />
                )}
            </div>

            {isUser && (
                <div className="w-8 h-8 rounded-full bg-zinc-700/50 flex items-center justify-center shrink-0 mt-1 border border-white/5">
                    <User size={16} className="text-zinc-300" />
                </div>
            )}
        </motion.div>
    );
}

function ToolExecution({ tool, input }: { tool: string; input?: any }) {
    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="max-w-3xl mx-auto pl-12"
        >
            <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-lg p-2 w-fit">
                <Terminal size={12} />
                <span className="font-mono text-blue-600 dark:text-blue-400">
                    {tool}
                </span>
                <span className="text-zinc-400">executed</span>
                <CheckCircle2 size={12} className="text-emerald-500 ml-1" />
            </div>
        </motion.div>
    );
}
