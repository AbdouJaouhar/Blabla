"use client";

import React from "react";

type Role = "user" | "assistant";

interface Props {
  role: Role;
  children: React.ReactNode;
}

export default function MessageBubble({ role, children }: Props) {
  const isUser = role === "user";

  return (
    <div
      className={
        "bubble-row " + (isUser ? "bubble-row-user" : "bubble-row-assistant")
      }
    >
      <div
        className={isUser ? "bubble bubble-user" : "bubble bubble-assistant"}
      >
        {children}
      </div>
    </div>
  );
}
