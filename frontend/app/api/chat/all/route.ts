import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json();
  const API_URL = process.env.API_URL;

  const res = await fetch(`${API_URL}/chat/all`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
