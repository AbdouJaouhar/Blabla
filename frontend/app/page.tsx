"use client";

import React from "react";
import Chat from "../components/Chat";
import ChatsList from "../components/ChatsList";

export default function HomePage() {
  return (
    <main className="flex h-screen w-screen text-white overflow-hidden">
      <ChatsList />
      <div className="flex-1 overflow-hidden">
        <Chat />
      </div>
    </main>
  );
}
