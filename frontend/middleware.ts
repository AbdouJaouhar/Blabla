import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const token = req.cookies.get("access_token")?.value;
  const pathname = req.nextUrl.pathname;

  const publicRoutes = ["/signin", "/signup", "/api"];
  const isPublic = publicRoutes.some((p) => pathname.startsWith(p));

  if (!isPublic && !token) {
    const url = new URL("/signin", req.url);
    return NextResponse.redirect(url);
  }

  if ((pathname === "/signin" || pathname === "/signup") && token) {
    const url = new URL("/", req.url);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|static|images|favicon.ico).*)"],
};
