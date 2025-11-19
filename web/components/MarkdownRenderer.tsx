"use client";

import React, { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import MermaidDiagram from "./MermaidDiagram";

interface Props {
    children: string;
    disableMermaid?: boolean;
}

function MarkdownRendererInner({ children, disableMermaid }: Props) {
    return (
        <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[
                [
                    rehypeKatex,
                    {
                        maxSize: 3,
                        trust: true,
                        strict: false,
                        output: "htmlAndMathml",
                    },
                ],
                rehypeHighlight as any,
            ]}
            components={{
                code: ({
                    node,
                    className = "",
                    children: codeChildren,
                    ...props
                }) => {
                    const [copied, setCopied] = useState(false);
                    const codeTextRef = useRef<HTMLSpanElement | null>(null);

                    const handleCopy = () => {
                        const text = codeTextRef.current?.innerText || "";
                        navigator.clipboard.writeText(text).then(() => {
                            setCopied(true);
                            setTimeout(() => setCopied(false), 1200);
                        });
                    };

                    const isBlock = className.includes("language-");
                    const isMermaid = className.includes("language-mermaid");

                    // ---------- Inline code ----------
                    if (!isBlock) {
                        return (
                            <code className="md-inline-code" {...props}>
                                {codeChildren}
                            </code>
                        );
                    }

                    // ---------- Mermaid block ----------
                    if (isMermaid) {
                        if (disableMermaid) {
                            return (
                                <div
                                    style={{
                                        position: "relative",
                                        minHeight: "4rem",
                                    }}
                                >
                                    <div className="mermaid-loading-box">
                                        <p>🔨</p>
                                        <p> Création du diagramme...</p>
                                    </div>
                                </div>
                            );
                        }

                        const raw =
                            (node as any)?.children?.[0]?.value ??
                            (Array.isArray(codeChildren)
                                ? codeChildren.join("")
                                : String(codeChildren));

                        return <MermaidDiagram code={String(raw)} />;
                    }

                    // ---------- Standard code block ----------
                    return (
                        <div
                            className="md-code-block-wrapper"
                            style={{ position: "relative" }}
                        >
                            <button
                                type="button"
                                className="md-block-code-cp-btn"
                                onClick={handleCopy}
                            >
                                {copied ? "copied" : "copy"}
                            </button>

                            <pre className={className}>
                                <code {...props}>
                                    <span ref={codeTextRef}>
                                        {codeChildren}
                                    </span>
                                </code>
                            </pre>
                        </div>
                    );
                },

                h1: ({ node, ...props }) => <h1 className="md-h1" {...props} />,
                h2: ({ node, ...props }) => <h2 className="md-h2" {...props} />,
                h3: ({ node, ...props }) => <h3 className="md-h3" {...props} />,
                p: ({ node, ...props }) => <p className="md-p" {...props} />,
                ul: ({ node, ...props }) => <ul className="md-ul" {...props} />,
                ol: ({ node, ...props }) => <ol className="md-ol" {...props} />,
                li: ({ node, ...props }) => <li className="md-li" {...props} />,
                blockquote: ({ node, ...props }) => (
                    <blockquote className="md-quote" {...props} />
                ),
                table: ({ node, ...props }) => (
                    <div className="md-table-wrapper">
                        <table {...props} />
                    </div>
                ),
            }}
        >
            {children}
        </ReactMarkdown>
    );
}

/**
 * Memoize so that typing outside doesn't re-render markdown/mermaid
 * unless `children` or `disableMermaid` actually change.
 */
const MarkdownRenderer = React.memo(
    MarkdownRendererInner,
    (prev, next) =>
        prev.children === next.children &&
        prev.disableMermaid === next.disableMermaid,
);

MarkdownRenderer.displayName = "MarkdownRenderer";

export default MarkdownRenderer;
