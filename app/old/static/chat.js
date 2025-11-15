const chatBox = document.getElementById("chat");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

function userIsNearBottom() {
    const wrapper = chatBox.parentElement;
    const threshold = 10; // px above bottom = stop autoscroll
    return (
        wrapper.scrollHeight - wrapper.scrollTop - wrapper.clientHeight <
        threshold
    );
}

function scrollToBottom() {
    const wrapper = chatBox.parentElement;
    if (userIsNearBottom()) {
        wrapper.scrollTop = wrapper.scrollHeight;
    }
}

function renderMarkdownAndMath(element, text) {
    // Render Markdown
    element.innerHTML = marked.parse(text);

    // Highlight code blocks
    element.querySelectorAll("pre code").forEach((block) => {
        hljs.highlightElement(block);
    });

    // Render KaTeX math
    renderMathInElement(element, {
        delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\[", right: "\\]", display: true },
            { left: "\\(", right: "\\)", display: false },
            { left: "[", right: "]", display: true },
        ],
    });
}

function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = "message " + role;
    renderMarkdownAndMath(div, text);
    chatBox.appendChild(div);
    scrollToBottom();
    return div;
}

async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    input.value = "";
    addMessage("user", msg);

    const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
    });

    const reader = response.body.getReader();
    let assistantText = "";
    let assistantDiv = addMessage("assistant", "");

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = new TextDecoder().decode(value);

        chunk.split("\n").forEach((line) => {
            if (!line.startsWith("data: ")) return;

            const data = line.replace("data: ", "").trim();
            if (data === "[DONE]") return;

            const obj = JSON.parse(data);
            assistantText += obj.token;

            renderMarkdownAndMath(assistantDiv, assistantText);
            scrollToBottom();
        });
    }
}

sendBtn.onclick = sendMessage;

input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
