"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp, Paperclip } from "lucide-react";
import { twMerge } from "tailwind-merge";

interface MessageInputProps {
    onSend: (message: string) => void;
    disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
    const [input, setInput] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || disabled) return;
        onSend(input);
        setInput("");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${Math.min(
                textareaRef.current.scrollHeight,
                200
            )}px`;
        }
    }, [input]);

    return (
        <form
            onSubmit={handleSubmit}
            className="relative flex items-end gap-2 p-1.5 bg-zinc-800/40 backdrop-blur-md border border-white/5 rounded-[2rem] focus-within:ring-1 focus-within:ring-white/10 focus-within:bg-zinc-800/60 transition-all duration-300 shadow-xl shadow-black/20"
        >
            <div className="pl-3 pb-3 text-zinc-500 hover:text-zinc-300 cursor-pointer transition-colors">
                <Paperclip size={20} />
            </div>
            <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask aero anything..."
                disabled={disabled}
                rows={1}
                data-gramm="false"
                className="flex-1 bg-transparent border-0 focus:ring-0 resize-none py-3 max-h-[200px] text-zinc-100 placeholder:text-zinc-600 disabled:opacity-50 text-base selection:bg-white/20"
            />
            <button
                type="submit"
                disabled={!input.trim() || disabled}
                className={twMerge(
                    "p-2.5 rounded-full transition-all duration-200 mb-0.5 mr-0.5 flex items-center justify-center",
                    input.trim() && !disabled
                        ? "bg-zinc-100 text-black hover:bg-white shadow-[0_0_15px_rgba(255,255,255,0.1)] active:scale-95"
                        : "bg-zinc-800/50 text-zinc-600 cursor-not-allowed"
                )}
            >
                <ArrowUp size={18} />
            </button>
        </form>
    );
}
