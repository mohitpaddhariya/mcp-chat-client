"use client";

import { useEffect, useState } from "react";
import { MCPInfo } from "../types";
import { Check, Server, RefreshCw, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface MCPSelectorProps {
    selectedMCPs: string[];
    onToggleMCP: (mcpType: string) => void;
}

export function MCPSelector({ selectedMCPs, onToggleMCP }: MCPSelectorProps) {
    const [mcps, setMcps] = useState<MCPInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchMCPs = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("http://127.0.0.1:8000/mcps");
            if (!res.ok) throw new Error("Failed to fetch MCPs");
            const data = await res.json();
            setMcps(data);
        } catch (err) {
            console.error(err);
            setError("Could not load MCP servers");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMCPs();
    }, []);

    return (
        <div className="w-full max-w-md space-y-4">
            <div className="flex items-center justify-between px-2">
                <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">
                    Available Tools
                </h3>
                <button
                    onClick={fetchMCPs}
                    className="p-1.5 rounded-lg hover:bg-zinc-800 transition-colors text-zinc-500 hover:text-zinc-300"
                    title="Refresh MCPs"
                >
                    <RefreshCw size={14} className={clsx({ "animate-spin": loading })} />
                </button>
            </div>

            {error && (
                <div className="flex items-center gap-2 text-sm text-red-400 bg-red-900/10 border border-red-900/20 p-3 rounded-lg">
                    <AlertCircle size={16} />
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 gap-2">
                <AnimatePresence>
                    {mcps.map((mcp) => {
                        const isSelected = selectedMCPs.includes(mcp.type);
                        return (
                            <motion.button
                                key={mcp.type}
                                initial={{ opacity: 0, y: 5 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0 }}
                                onClick={() => onToggleMCP(mcp.type)}
                                className={twMerge(
                                    "group relative flex items-center justify-between p-3 rounded-xl border transition-all duration-200 text-left",
                                    isSelected
                                        ? "bg-blue-500/10 border-blue-500/30"
                                        : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900"
                                )}
                            >
                                <div className="flex items-center gap-3">
                                    <div
                                        className={twMerge(
                                            "p-2 rounded-lg transition-colors",
                                            isSelected
                                                ? "bg-blue-500/20 text-blue-400"
                                                : "bg-zinc-800 text-zinc-500 group-hover:text-zinc-300"
                                        )}
                                    >
                                        <Server size={18} />
                                    </div>
                                    <div>
                                        <div className="font-medium text-zinc-200">
                                            {mcp.name}
                                        </div>
                                        <div className="text-xs text-zinc-500 mt-0.5">
                                            {mcp.tools.length} tools available
                                        </div>
                                    </div>
                                </div>

                                <div
                                    className={twMerge(
                                        "w-5 h-5 rounded-full border flex items-center justify-center transition-colors",
                                        isSelected
                                            ? "bg-blue-500 border-blue-500 text-white"
                                            : "border-zinc-700 bg-zinc-900/50"
                                    )}
                                >
                                    {isSelected && <Check size={12} strokeWidth={3} />}
                                </div>
                            </motion.button>
                        );
                    })}
                </AnimatePresence>

                {!loading && mcps.length === 0 && !error && (
                    <div className="text-center py-8 text-zinc-600 text-sm">
                        No MCP servers found.
                    </div>
                )}
            </div>
        </div>
    );
}
