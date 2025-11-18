import { useState } from "react";

export default function useChatStreaming(messages, setMessages, cleanLatex) {
    const [isStreaming, setIsStreaming] = useState(false);

    async function sendChatRequest(
        text: string,
        images: string[],
        assistantId: string,
    ) {
        setIsStreaming(true);

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, images }),
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

                        let parsed;
                        try {
                            parsed = JSON.parse(dataStr);
                        } catch {
                            continue;
                        }

                        if (!parsed.token) continue;

                        const token = parsed.token;

                        setMessages((prev) =>
                            prev.map((m) =>
                                m.id === assistantId
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
        } finally {
            setIsStreaming(false);
            setMessages((prev) =>
                prev.map((m) =>
                    m.id === assistantId ? { ...m, streaming: false } : m,
                ),
            );
        }
    }

    return { isStreaming, sendChatRequest };
}
