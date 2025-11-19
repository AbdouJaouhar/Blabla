"use client";

import React, { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { OrbitProgress } from "react-loading-indicators";

interface MermaidDiagramProps {
  code: string;
}

let mermaidInitialized = false;

if (typeof window !== "undefined" && !mermaidInitialized) {
  mermaid.initialize({
    startOnLoad: false,
    theme: "base",
  });
  mermaidInitialized = true;
}

const MermaidDiagram: React.FC<MermaidDiagramProps> = React.memo(({ code }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [ready, setReady] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !ref.current) return;

    let alive = true;
    const el = ref.current;

    const renderDiagram = async () => {
      setReady(false);

      try {
        const trimmed = code.trim();

        await mermaid.parse(trimmed);

        const { svg } = await mermaid.render(
          "m-" + Math.random().toString(36).slice(2),
          trimmed,
        );

        if (!alive) return;
        el.innerHTML = svg;
      } catch {
        if (alive) {
          el.innerHTML =
            '<pre className="mermaid-error">Invalid Mermaid syntax</pre>';
        }
      }

      if (alive) {
        requestAnimationFrame(() => setReady(true));
      }
    };

    void renderDiagram();

    return () => {
      alive = false;
    };
  }, [code, mounted]);

  if (!mounted) {
    return (
      <div
        style={{
          position: "relative",
          minHeight: "4rem",
        }}
      >
        <div className="mermaid-loading-box">
          <OrbitProgress size="small" color={"#10a37f"} />
          <p> Création du diagramme...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: "relative",
        minHeight: ready ? undefined : "4rem",
        background: "white",
        borderRadius: "0.5rem",
        padding: "1rem",
      }}
    >
      {!ready && (
        <div
          style={{
            position: "relative",
            minHeight: "4rem",
          }}
        >
          <div className="mermaid-loading-box">
            <OrbitProgress size="small" color={"#10a37f"} />
            <p> Création du diagramme...</p>
          </div>
        </div>
      )}

      <div
        ref={ref}
        style={{
          visibility: ready ? "visible" : "hidden",
        }}
      />
    </div>
  );
});

MermaidDiagram.displayName = "MermaidDiagram";

export default MermaidDiagram;
