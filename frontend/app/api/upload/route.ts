// app/api/upload/route.ts
import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import sharp from "sharp";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
    try {
        const formData = await req.formData();
        const file = formData.get("file") as File | null;

        if (!file) {
            return NextResponse.json(
                { error: "No file uploaded" },
                { status: 400 },
            );
        }

        const arrayBuffer = await file.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);

        // --- resize if needed ---------------------------------------------
        const resized = await sharp(buffer)
            .resize(512, 512, {
                // 512 px max on the longer side
                fit: "inside", // keep aspect ratio
                withoutEnlargement: true, // never blow a small image up
            })
            .toBuffer();
        // -------------------------------------------------------------------

        const uploadDir = path.join(process.cwd(), "public/uploads");
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
        }

        const ext = file.name.split(".").pop()?.toLowerCase() || "jpg";
        const filename = `${Date.now()}-${Math.random()
            .toString(36)
            .slice(2)}.${ext}`;
        const filepath = path.join(uploadDir, filename);

        fs.writeFileSync(filepath, resized); // save the resized version

        return NextResponse.json({ url: `/uploads/${filename}` });
    } catch (err) {
        console.error("UPLOAD ERROR:", err);
        return NextResponse.json({ error: "Upload failed" }, { status: 500 });
    }
}
