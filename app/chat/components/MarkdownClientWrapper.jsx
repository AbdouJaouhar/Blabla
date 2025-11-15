"use client";

import dynamic from "next/dynamic";

const MarkdownRenderer = dynamic(() => import("./MarkdownRenderer"), {
    ssr: true,
});

export default function MarkdownClientWrapper({ content }) {
    return <MarkdownRenderer content={content} />;
}
