"use client";

import React, { FormEvent, useEffect, useRef, useState } from "react";
import MarkdownRenderer from "./MarkdownRenderer";
import MessageBubble from "./MessageBubble"; // assuming this exists
import { v4 as uuid } from "uuid";
type Role = "user" | "assistant";

interface Message {
    id: string;
    role: Role;
    content: string;
    streaming: boolean;
}

const API_URL = "/api/chat";

/**
 * LaTeX cleaner
 */
export function cleanLatex(text: string): string {
    if (typeof text !== "string") return text;
    text = text.replace(/\\\(([\s\S]*?)\\\)/g, (_, inner) => `$${inner}$`);
    text = text.replace(/\\\[([\s\S]*?)\\\]/g, (_, inner) => `$${inner}$`);
    return text;
}

export default function Chat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);

    // Scroll handling
    const containerRef = useRef<HTMLDivElement | null>(null);
    const messagesEndRef = useRef<HTMLDivElement | null>(null);
    const scrollTimeout = useRef<NodeJS.Timeout | null>(null);
    const [autoScroll, setAutoScroll] = useState(true);

    const scrollToBottom = () => {
        if (scrollTimeout.current) clearTimeout(scrollTimeout.current);

        scrollTimeout.current = setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({
                behavior: "smooth",
            });
        }, 50);
    };

    // Detect user manual scroll → toggle autoScroll
    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        const handleScroll = () => {
            const nearBottom =
                el.scrollHeight - el.scrollTop - el.clientHeight < 80;
            setAutoScroll(nearBottom);
        };

        el.addEventListener("scroll", handleScroll);
        return () => el.removeEventListener("scroll", handleScroll);
    }, []);

    // Scroll when messages change and autoScroll is true
    useEffect(() => {
        if (autoScroll) scrollToBottom();
    }, [messages, autoScroll]);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isStreaming) return;

        const userMessage: Message = {
            id: uuid(),
            role: "user",
            content: input.trim(),
            streaming: false,
        };

        const assistantMessage: Message = {
            id: uuid(),
            role: "assistant",
            content: "",
            streaming: true,
        };

        setMessages((prev) => [...prev, userMessage, assistantMessage]);
        setInput("");
        setIsStreaming(true);

        try {
            const res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage.content }),
            });

            if (!res.body) throw new Error("No response body");

            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split("\n\n");
                buffer = parts.pop() ?? "";

                for (const part of parts) {
                    const lines = part.split("\n");
                    for (const line of lines) {
                        if (!line.startsWith("data:")) continue;

                        const dataStr = line.slice(5).trim();
                        if (!dataStr || dataStr === "[DONE]") continue;

                        let parsed: { token?: string };
                        try {
                            parsed = JSON.parse(dataStr);
                        } catch {
                            continue;
                        }

                        if (!parsed.token) continue;
                        const token = parsed.token;

                        setMessages((prev) =>
                            prev.map((m) =>
                                m.id === assistantMessage.id
                                    ? {
                                          ...m,
                                          content: cleanLatex(
                                              m.content + token,
                                          ),
                                      }
                                    : m,
                            ),
                        );
                    }
                }
            }
        } catch (err) {
            console.error("Streaming error:", err);
            setMessages((prev) => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content:
                        "⚠️ An error occurred while contacting the server.",
                    streaming: false,
                },
            ]);
        } finally {
            setIsStreaming(false);
            setMessages((prev) =>
                prev.map((m) =>
                    m.role === "assistant" && m.streaming
                        ? { ...m, streaming: false }
                        : m,
                ),
            );
        }
    };

    return (
        <div className="chat-container">
            {messages.length === 0 ? (
                <div className="chat-empty">
                    <p className="chat-empty-prompt">Hey, how you doing ?</p>

                    <form className="chat-input-row" onSubmit={handleSubmit}>
                        <textarea
                            className="chat-input"
                            value={input}
                            placeholder="Ask a question"
                            rows={1}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    void handleSubmit(
                                        e as unknown as FormEvent,
                                    );
                                }
                            }}
                        />
                    </form>
                </div>
            ) : (
                <>
                    <div className="chat-messages" ref={containerRef}>
                        {messages.map((msg) => (
                            <MessageBubble key={msg.id} role={msg.role}>
                                <MarkdownRenderer
                                    disableMermaid={msg.streaming}
                                >
                                    {msg.content}
                                </MarkdownRenderer>
                            </MessageBubble>
                        ))}

                        <div ref={messagesEndRef} />
                    </div>

                    <form
                        className="chat-input-row sticky bottom-0 bg-white"
                        onSubmit={handleSubmit}
                    >
                        <textarea
                            className="chat-input"
                            value={input}
                            placeholder="Ask a question"
                            rows={1}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    void handleSubmit(
                                        e as unknown as FormEvent,
                                    );
                                }
                            }}
                        />
                    </form>
                </>
            )}
        </div>
    );
}
