import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypePrettyCode from "rehype-pretty-code";
import { codeToHtml } from "shiki";

export async function highlight(code, lang = "text") {
    return await codeToHtml(code, {
        lang,
        theme: "github-dark",
    });
}

export default function MarkdownRenderer({ content }) {
    async function CodeBlock({ children, className }) {
        const lang = className?.replace("language-", "") || "text";
        const code = String(children).trim();

        const html = await highlight(code, lang);

        return (
            <div
                className="my-4 border border-zinc-800 rounded-xl bg-black"
                dangerouslySetInnerHTML={{ __html: html }}
            />
        );
    }

    return (
        <div
            className="prose prose-invert max-w-none
            prose-headings:font-semibold
            prose-headings:text-white
            prose-p:text-zinc-200
            prose-strong:text-white
            prose-code:text-[0.9rem]
            prose-code:bg-zinc-800
            prose-code:px-1.5
            prose-code:py-0.5
            prose-code:rounded
            prose-pre:bg-[#0d0d0d]
            prose-pre:border
            prose-pre:border-zinc-800
            prose-pre:rounded-xl
            prose-pre:p-0"
        >
            <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                    code: CodeBlock,
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
