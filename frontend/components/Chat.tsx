"use client";

import React, { useRef, useState, useEffect } from "react";
import { v4 as uuid } from "uuid";
import type { Message } from "../utils/types";
import { cleanLatex } from "../utils/latex";

import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import useChatStreaming from "./useChatStreaming";
import { PendingImage } from "../utils/types";

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [pendingImages, setPendingImages] = useState<PendingImage[]>([]);
  const [input, setInput] = useState("");

  const containerRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const { isStreaming, sendChatRequest } = useChatStreaming(
    messages,
    setMessages,
    cleanLatex,
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleScroll = () => {
      const isNearBottom =
        el.scrollHeight - el.scrollTop - el.clientHeight < 80;
      setAutoScroll(isNearBottom);
    };

    el.addEventListener("scroll", handleScroll);
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    if (!autoScroll) return;
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, autoScroll]);

  const handleSubmit = async () => {
    const text = input.trim();
    if ((!text && pendingImages.length === 0) || isStreaming) return;

    const imgMarkdown = pendingImages
      .map((url) => `![image](${url})`)
      .join("\n\n");

    const displayContent = [text, imgMarkdown].filter(Boolean).join("\n\n");

    const userMessage: Message = {
      id: uuid(),
      role: "user",
      content: displayContent,
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
    setPendingImages([]);

    await sendChatRequest(text, pendingImages, assistantMessage.id);
  };

  return (
    <div className="chat-container">
      <MessageList
        messages={messages}
        containerRef={containerRef}
        messagesEndRef={messagesEndRef}
      />

      <ChatInput
        input={input}
        setInput={setInput}
        pendingImages={pendingImages}
        setPendingImages={setPendingImages}
        onSubmit={handleSubmit}
        disabled={isStreaming}
      />
    </div>
  );
}
