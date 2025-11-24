"use client";

import React, { useState, useEffect } from "react";
import {
  Plus,
  PanelLeftOpen,
  PanelLeftClose,
  MessageSquare,
  Settings,
} from "lucide-react";

export default function ChatsList() {
  const [open, setOpen] = useState(true);
  const [chats, setChats] = useState([]);

  useEffect(() => {
    async function load() {
      const r = await fetch("/api/chats/all");
      if (!r.ok) return;
      const d = await r.json();
      setChats(d);
    }
    load();
  }, []);

  async function createChat() {
    const r = await fetch("/api/chats/new", { method: "POST" });
    if (!r.ok) return;
    const newChat = await r.json();
    setChats([newChat, ...chats]);
  }

  const sidebarWidth = open ? "w-[260px]" : "w-[64px]";

  const buttonBase =
    "flex items-center gap-3 h-10 rounded-md bg-[#2F2F35] hover:bg-[#3A3A41] transition-colors duration-200";
  const iconButton =
    "flex items-center justify-center h-10 w-10 rounded-md bg-[#2F2F35] hover:bg-[#3A3A41] transition-colors duration-200";

  return (
    <aside
      className={`h-full flex flex-col bg-[#1F1F25] border-r border-white/5 transition-all duration-300 ${sidebarWidth}`}
    >
      <div className="p-3">
        {open ? (
          <button
            onClick={() => setOpen(false)}
            className={buttonBase + " w-full justify-start px-3"}
          >
            <PanelLeftClose size={18} />
            <span className="text-sm">Collapse</span>
          </button>
        ) : (
          <button onClick={() => setOpen(true)} className={iconButton}>
            <PanelLeftOpen size={18} />
          </button>
        )}
      </div>

      <div className="px-3">
        {open ? (
          <button
            onClick={createChat}
            className={buttonBase + " w-full justify-start px-3 text-sm"}
          >
            <Plus size={18} />
            New Chat
          </button>
        ) : (
          <button onClick={createChat} className={iconButton}>
            <Plus size={18} />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 mt-3 space-y-1">
        {chats.map((c) =>
          open ? (
            <button
              key={c.id}
              className="flex items-center gap-3 w-full rounded-md px-3 py-2 text-sm hover:bg-[#2A2B32] transition-colors duration-200"
            >
              <MessageSquare size={18} />
              <span className="truncate">{c.title}</span>
            </button>
          ) : (
            <button key={c.id} className={iconButton}>
              <MessageSquare size={18} />
            </button>
          ),
        )}
      </div>

      <div className="px-3 py-3 border-t border-white/5">
        {open ? (
          <button className={buttonBase + " w-full justify-start px-3 text-sm"}>
            <Settings size={18} />
            Settings
          </button>
        ) : (
          <button className={iconButton}>
            <Settings size={18} />
          </button>
        )}
      </div>
    </aside>
  );
}
