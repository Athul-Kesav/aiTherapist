import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import FormData from "form-data";

export const runtime = "nodejs"; // ensure server runtime

// --------------------
// Types
// --------------------
interface TTSResult {
    data: string[]; // HF Space returns array of URLs
}

interface TTSRequestBody {
    text: string;
}

// --------------------
// TTS Caller
// --------------------
async function callChatterboxTTS(text: string, audioPromptPath?: string): Promise<Buffer> {
    const form = new FormData();

    form.append("text_input", text);
    form.append("exaggeration_input", "0.5");
    form.append("temperature_input", "0.8");
    form.append("seed_num_input", "0");
    form.append("cfgw_input", "0.5");
    form.append("vad_trim_input", "false");

    // Optional voice prompt
    if (audioPromptPath && fs.existsSync(audioPromptPath)) {
        const fileData = fs.readFileSync(audioPromptPath);
        const uint8 = new Uint8Array(fileData); // VALID BlobPart

        form.append("audio_prompt_path_input", uint8, "Sample_Voice.mpeg");
    }

    const res = await fetch("https://ressembleai-chatterbox.hf.space/api/predict", {
        method: "POST",
        body: form as unknown as BodyInit, // Node FormData workaround
        headers: form.getHeaders(),
    });

    const result = (await res.json()) as TTSResult;

    const fileUrl = result.data[0];

    const audioRes = await fetch(fileUrl);
    const audioArrayBuffer = await audioRes.arrayBuffer();
    return Buffer.from(audioArrayBuffer);
}

// --------------------
// POST Handler
// --------------------
export async function POST(req: Request): Promise<NextResponse> {
    try {
        const body = (await req.json()) as TTSRequestBody;

        if (!body.text) {
            return NextResponse.json(
                { error: "Missing 'text' field in request body" },
                { status: 400 }
            );
        }

        const testVoiceFile = path.join(process.cwd(), "Sample_Voice.mpeg");

        const audioBuffer = await callChatterboxTTS(body.text, testVoiceFile);

        return NextResponse.json({
            text: body.text,
            audioBase64: audioBuffer.toString("base64"),
            mime: "audio/mpeg",
        });
    } catch (err) {
        const error = err as Error;
        return NextResponse.json(
            { error: "TTS failed", details: error.message },
            { status: 500 }
        );
    }
}

// --------------------
// OPTIONS (CORS)
// --------------------
export async function OPTIONS(): Promise<NextResponse> {
    const res = new NextResponse(null, { status: 200 });
    res.headers.set("Access-Control-Allow-Origin", "*");
    res.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.headers.set("Access-Control-Allow-Headers", "Content-Type");
    return res;
}
