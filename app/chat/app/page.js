"use client";

import React, { useState, useRef, useEffect } from "react";
import {
    Send,
    Plus,
    MessageSquare,
    Trash2,
    Edit2,
    Check,
    X,
    Menu,
    ChevronLeft,
} from "lucide-react";
import MarkdownClientWrapper from "@/components/MarkdownClientWrapper";

export default function ChatInterface() {
    const [conversations, setConversations] = useState([
        {
            id: 1,
            title: "New Conversation",
            messages: [],
            createdAt: Date.now(),
        },
    ]);
    const [activeConvId, setActiveConvId] = useState(1);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [editTitle, setEditTitle] = useState("");
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const activeConv = conversations.find((c) => c.id === activeConvId);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [activeConv?.messages]);

    const generateTitle = (message) => {
        const words = message.split(" ").slice(0, 6).join(" ");
        return words.length < message.length ? words + "..." : words;
    };

    const createNewConversation = () => {
        const newId = Math.max(...conversations.map((c) => c.id), 0) + 1;
        const newConv = {
            id: newId,
            title: "New Conversation",
            messages: [],
            createdAt: Date.now(),
        };
        setConversations([newConv, ...conversations]);
        setActiveConvId(newId);
    };

    const deleteConversation = (id) => {
        if (conversations.length === 1) return;
        const filtered = conversations.filter((c) => c.id !== id);
        setConversations(filtered);
        if (activeConvId === id) {
            setActiveConvId(filtered[0].id);
        }
    };

    const startEdit = (id, title) => {
        setEditingId(id);
        setEditTitle(title);
    };

    const saveEdit = (id) => {
        setConversations(
            conversations.map((c) =>
                c.id === id ? { ...c, title: editTitle.trim() || c.title } : c,
            ),
        );
        setEditingId(null);
    };

    const cancelEdit = () => {
        setEditingId(null);
        setEditTitle("");
    };

    // ------------------------------------------------------------------
    //  SEND MESSAGE WITH STREAMING SUPPORT (SSE)
    // ------------------------------------------------------------------
    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = { role: "user", content: input.trim() };
        const updatedMessages = [...activeConv.messages, userMessage];

        setConversations((prev) =>
            prev.map((c) =>
                c.id === activeConvId
                    ? {
                          ...c,
                          messages: updatedMessages,
                          title:
                              c.messages.length === 0
                                  ? generateTitle(input)
                                  : c.title,
                      }
                    : c,
            ),
        );

        setInput("");
        setIsLoading(true);

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: input }),
            });

            if (!response.ok) throw new Error("API request failed");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let assistantText = "";

            // Add initial empty assistant message for streaming updates
            setConversations((prev) =>
                prev.map((c) =>
                    c.id === activeConvId
                        ? {
                              ...c,
                              messages: [
                                  ...updatedMessages,
                                  { role: "assistant", content: "" },
                              ],
                          }
                        : c,
                ),
            );

            // STREAM LOOP
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n");

                for (let line of lines) {
                    if (!line.startsWith("data:")) continue;

                    const jsonStr = line.replace("data:", "").trim();
                    if (!jsonStr) continue;

                    let payload;
                    try {
                        payload = JSON.parse(jsonStr);
                    } catch {
                        continue;
                    }

                    if (payload.token) {
                        assistantText += payload.token;

                        setConversations((prev) =>
                            prev.map((c) =>
                                c.id === activeConvId
                                    ? {
                                          ...c,
                                          messages: [
                                              ...updatedMessages,
                                              {
                                                  role: "assistant",
                                                  content: assistantText,
                                              },
                                          ],
                                      }
                                    : c,
                            ),
                        );
                    }
                }
            }
        } catch (error) {
            console.error("Streaming Error:", error);

            setConversations((prev) =>
                prev.map((c) =>
                    c.id === activeConvId
                        ? {
                              ...c,
                              messages: [
                                  ...updatedMessages,
                                  {
                                      role: "assistant",
                                      content:
                                          "Error: backend server unavailable.",
                                  },
                              ],
                          }
                        : c,
                ),
            );
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // ------------------------------------------------------------------
    //  UI Rendering
    // ------------------------------------------------------------------

    return (
        <div className="flex h-screen bg-black text-white">
            {/* Sidebar */}
            <div
                className={`${sidebarOpen ? "w-64" : "w-0"} transition-all duration-300 bg-black border-r border-zinc-800 flex flex-col overflow-hidden`}
            >
                <div className="p-4 border-b border-zinc-800">
                    <button
                        onClick={createNewConversation}
                        className="w-full flex items-center gap-2 px-4 py-3 bg-zinc-900 hover:bg-zinc-800 rounded-lg transition-colors"
                    >
                        <Plus size={18} />
                        <span>New Chat</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-2">
                    {conversations.map((conv) => (
                        <div
                            key={conv.id}
                            className={`group flex items-center gap-2 p-3 mb-1 rounded-lg cursor-pointer transition-colors ${
                                activeConvId === conv.id
                                    ? "bg-zinc-900"
                                    : "hover:bg-zinc-900"
                            }`}
                            onClick={() => setActiveConvId(conv.id)}
                        >
                            <MessageSquare size={16} />

                            {editingId === conv.id ? (
                                <div className="flex-1 flex items-center gap-1">
                                    <input
                                        type="text"
                                        value={editTitle}
                                        onChange={(e) =>
                                            setEditTitle(e.target.value)
                                        }
                                        className="flex-1 bg-zinc-800 px-2 py-1 rounded text-sm outline-none"
                                        autoFocus
                                    />
                                    <button
                                        onClick={() => saveEdit(conv.id)}
                                        className="p-1 hover:bg-zinc-800 rounded"
                                    >
                                        <Check size={14} />
                                    </button>
                                    <button
                                        onClick={cancelEdit}
                                        className="p-1 hover:bg-zinc-800 rounded"
                                    >
                                        <X size={14} />
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <span className="flex-1 text-sm truncate">
                                        {conv.title}
                                    </span>
                                    <div className="hidden group-hover:flex gap-1">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                startEdit(conv.id, conv.title);
                                            }}
                                            className="p-1 hover:bg-zinc-800 rounded"
                                        >
                                            <Edit2 size={14} />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                deleteConversation(conv.id);
                                            }}
                                            className="p-1 hover:bg-red-600 rounded"
                                            disabled={
                                                conversations.length === 1
                                            }
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Chat Window */}
            <div className="flex-1 flex flex-col">
                {/* Header */}
                <div className="h-14 border-b border-zinc-800 flex items-center px-4 gap-3">
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-2 hover:bg-zinc-900 rounded-lg transition-colors"
                    >
                        {sidebarOpen ? (
                            <ChevronLeft size={20} />
                        ) : (
                            <Menu size={20} />
                        )}
                    </button>
                    <h1 className="text-lg font-semibold">
                        {activeConv?.title}
                    </h1>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto">
                    {activeConv?.messages.length === 0 ? (
                        <div className="h-full flex items-center justify-center text-zinc-500">
                            <MessageSquare
                                size={48}
                                className="mx-auto mb-4 opacity-50"
                            />
                            <p className="text-lg">Start a new conversation</p>
                        </div>
                    ) : (
                        <div className="max-w-3xl mx-auto px-4 py-8">
                            {activeConv.messages.map((msg, idx) => (
                                <div
                                    key={idx}
                                    className={`mb-8 ${
                                        msg.role === "user" ? "text-right" : ""
                                    }`}
                                >
                                    <div
                                        className={`inline-block max-w-[80%] ${
                                            msg.role === "user"
                                                ? "bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3"
                                                : "bg-zinc-900 rounded-2xl rounded-tl-sm px-4 py-3"
                                        }`}
                                    >
                                        {msg.role === "assistant" ? (
                                            <MarkdownClientWrapper
                                                content={msg.content}
                                            />
                                        ) : (
                                            <div className="whitespace-pre-wrap break-words">
                                                {msg.content}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className="mb-8">
                                    <div className="inline-block bg-zinc-900 rounded-2xl px-4 py-3">
                                        <div className="flex gap-1">
                                            <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"></div>
                                            <div
                                                className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"
                                                style={{
                                                    animationDelay: "150ms",
                                                }}
                                            ></div>
                                            <div
                                                className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"
                                                style={{
                                                    animationDelay: "300ms",
                                                }}
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Input field */}
                <div className="border-t border-zinc-800 p-4">
                    <div className="max-w-3xl mx-auto">
                        <div className="flex gap-3 items-end bg-zinc-900 rounded-2xl px-4 py-3">
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Message..."
                                className="flex-1 bg-transparent outline-none resize-none max-h-32 text-white placeholder-zinc-500"
                                rows={1}
                                style={{ minHeight: "24px", height: "auto" }}
                                onInput={(e) => {
                                    e.target.style.height = "auto";
                                    e.target.style.height =
                                        e.target.scrollHeight + "px";
                                }}
                            />
                            <button
                                onClick={sendMessage}
                                disabled={!input.trim() || isLoading}
                                className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-800 rounded-lg transition-colors"
                            >
                                <Send size={18} />
                            </button>
                        </div>

                        <p className="text-xs text-zinc-500 text-center mt-2">
                            Backend endpoint: http://localhost:3001/api/chat
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
