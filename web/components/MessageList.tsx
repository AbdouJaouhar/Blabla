import React from "react";
import MessageBubble from "./MessageBubble";
import MarkdownRenderer from "./MarkdownRenderer";
import type { Message } from "../utils/types";

type Props = {
    messages: Message[];
    containerRef: React.RefObject<HTMLDivElement>;
    messagesEndRef: React.RefObject<HTMLDivElement>;
};

export default function MessageList({
    messages,
    containerRef,
    messagesEndRef,
}: Props) {
    return (
        <div className="chat-messages" ref={containerRef}>
            {messages.map((msg) => (
                <MessageBubble key={msg.id} role={msg.role}>
                    <div className="chat-message prose-img:max-w-[240px] prose-img:rounded-xl">
                        <MarkdownRenderer disableMermaid={msg.streaming}>
                            {msg.content}
                        </MarkdownRenderer>
                    </div>
                </MessageBubble>
            ))}
            <div ref={messagesEndRef} />
        </div>
    );
}
