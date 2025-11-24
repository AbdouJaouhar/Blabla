"use client";

import React, { useState } from "react";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || password !== confirm) return;

    setLoading(true);
    setError("");

    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    setLoading(false);

    if (!res.ok) {
      setError(data?.detail || "Signup failed");
      return;
    }
  };

  return (
    <div className="chat-shell">
      <div
        className="chat-container"
        style={{ justifyContent: "center", alignItems: "center" }}
      >
        <div className="chat-box" style={{ padding: "2rem", gap: "1.4rem" }}>
          <h1 style={{ margin: 0, fontSize: "1.8rem", fontWeight: 600 }}>
            Create your account
          </h1>

          {error && (
            <p style={{ color: "#ff6b6b", margin: 0, fontSize: "0.9rem" }}>
              {error}
            </p>
          )}

          <form
            onSubmit={handleSubmit}
            style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}
          >
            <input
              type="email"
              className="chat-box-textarea"
              placeholder="Email"
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
              inputMode="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                border: "1px solid var(--input-border)",
                padding: "0.8rem 1rem",
                borderRadius: "0.6rem",
                background: "var(--input-bg)",
              }}
            />

            <input
              type="password"
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
              inputMode="text"
              className="chat-box-textarea"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                border: "1px solid var(--input-border)",
                padding: "0.8rem 1rem",
                borderRadius: "0.6rem",
                background: "var(--input-bg)",
              }}
            />

            <input
              type="password"
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
              inputMode="text"
              className="chat-box-textarea"
              placeholder="Confirm password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              style={{
                border: "1px solid var(--input-border)",
                padding: "0.8rem 1rem",
                borderRadius: "0.6rem",
                background: "var(--input-bg)",
              }}
            />

            <button
              type="submit"
              className="chat-send-btn"
              disabled={
                loading ||
                !email ||
                !password ||
                !confirm ||
                password !== confirm
              }
              style={{
                width: "100%",
                justifyContent: "center",
                padding: "0.8rem 0",
              }}
            >
              {loading ? "Loading..." : "Sign up"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
