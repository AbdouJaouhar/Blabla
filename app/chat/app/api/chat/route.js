export async function POST(req) {
    const body = await req.json();

    const response = await fetch("http://localhost:3001/api/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    // Re-stream the SSE response
    const readable = new ReadableStream({
        async start(controller) {
            const reader = response.body.getReader();
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                controller.enqueue(value);
            }
            controller.close();
        },
    });

    return new Response(readable, {
        headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
        },
    });
}
