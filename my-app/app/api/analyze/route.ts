import { NextResponse } from "next/server";
import axios from "axios";
import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import FormData from "form-data";

dotenv.config();

const AI_MODEL = process.env.AI_MODEL ?? "";
const llmEndpoint = process.env.LLM_ENDPOINT ?? "";
const audioVideoEndpoint = process.env.AUDIO_VIDEO_ENDPOINT ?? "";

// -----------------------
//  Types
// -----------------------
interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

interface AnalyzeResponse {
  face_emotion?: string;
  voice_emotion?: string;
  transcription?: string;
}

// -----------------------
//  Message History Storage
// -----------------------
const historyFile = path.join(
  process.cwd(),
  "app/api/analyze/chat_history.json"
);

function loadHistory(): ChatMessage[] {
  if (fs.existsSync(historyFile)) {
    try {
      const txt = fs.readFileSync(historyFile, "utf-8").trim();
      return txt ? (JSON.parse(txt) as ChatMessage[]) : [];
    } catch {
      return [];
    }
  }
  return [];
}

function saveHistory(messages: ChatMessage[]): void {
  fs.writeFileSync(historyFile, JSON.stringify(messages, null, 2), "utf-8");
}

// -----------------------
//  System Prompt
// -----------------------
const systemPrompt = `
You are an empathetic, human-like AI mental-health assistant called "EmpathAIse".
Your tone is warm, non-judgmental, concise, and genuine.

RULES:
1. Reflect the user's emotion briefly.
2. Validate their feeling.
3. Offer ONE practical coping step.
4. Ask ONE gentle clarifying question only if needed.
5. Avoid diagnoses.
6. Crisis:
   - Ask if they are safe now.
   - If danger → contact emergency services.
7. Offer professional help if appropriate.
8. End with warmth.
9. Keep responses 2–6 sentences max.
`.trim();

// -----------------------
//  TTS Function
// -----------------------
async function callChatterboxTTS(
  text: string,
  audioPromptPath?: string
): Promise<Buffer> {
  const form = new FormData();

  form.append("text_input", text);
  form.append("exaggeration_input", "0.5");
  form.append("temperature_input", "0.8");
  form.append("seed_num_input", "0");
  form.append("cfgw_input", "0.5");
  form.append("vad_trim_input", "false");

  if (audioPromptPath && fs.existsSync(audioPromptPath)) {
    const fileData = fs.readFileSync(audioPromptPath);
    const uint8 = new Uint8Array(fileData);
    form.append("audio_prompt_path_input", uint8, "Sample_Voice.mpeg");
  }

  const res = await fetch(
    "https://ressembleai-chatterbox.hf.space/api/predict",
    {
      method: "POST",
      body: form as unknown as BodyInit,
      headers: form.getHeaders(),
    }
  );

  const result = (await res.json()) as { data: string[] };
  const fileUrl = result.data[0];

  const audioRes = await fetch(fileUrl);
  const audioBuffer = Buffer.from(await audioRes.arrayBuffer());

  return audioBuffer;
}

// -----------------------
//  CORS
// -----------------------
export async function OPTIONS() {
  const res = new NextResponse(null, { status: 200 });
  return withCors(res);
}

function withCors(res: NextResponse): NextResponse {
  res.headers.set("Access-Control-Allow-Origin", "*");
  res.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.headers.set("Access-Control-Allow-Headers", "Content-Type");
  return res;
}

// -----------------------
//  GET
// -----------------------
export async function GET() {
  return withCors(NextResponse.json({ message: "Backend online." }));
}

// -----------------------
//  POST (text or video)
// -----------------------
export async function POST(req: Request): Promise<NextResponse> {
  try {
    const formData = await req.formData();
    const textPrompt = formData.get("textPrompt") as string | null;
    const fileField = formData.get("file") as File | null;

    const messages = loadHistory();

    if (messages.length === 0) {
      messages.push({ role: "system", content: systemPrompt });
    }

    // =============== TEXT MESSAGE ===============
    if (textPrompt && !fileField) {
      messages.push({ role: "user", content: textPrompt });

      const llmResponse = await axios.post(
        `${llmEndpoint}/api/chat`,
        {
          model: AI_MODEL,
          messages,
          max_tokens: 80,
          temperature: 0.8,
          top_p: 0.5,
        },
        { headers: { "Content-Type": "application/json" } }
      );

      const reply: string =
        llmResponse.data?.message?.content ?? "No response.";

      messages.push({ role: "assistant", content: reply });
      saveHistory(messages);

      return withCors(NextResponse.json({ response: reply }));
    }

    // =============== VIDEO MESSAGE ===============
    if (!fileField) {
      return withCors(
        NextResponse.json({ error: "Missing video file." }, { status: 400 })
      );
    }

    const arrayBuffer = await fileField.arrayBuffer();
    const videoBuffer = Buffer.from(arrayBuffer);

    const fd = new FormData();
    fd.append(
      "file",
      new Blob([videoBuffer], { type: fileField.type }),
      fileField.name
    );

    const audioVideoResponse = await fetch(`${audioVideoEndpoint}/analyze`, {
      method: "POST",
      body: fd as unknown as BodyInit,
    });

    const audioVideoData =
      (await audioVideoResponse.json()) as AnalyzeResponse;

    const userMsg = `
Face emotion: ${audioVideoData.face_emotion ?? "neutral"}
Voice emotion: ${audioVideoData.voice_emotion ?? "neutral"}
Transcript: "${audioVideoData.transcription ?? ""}"
`.trim();

    messages.push({ role: "user", content: userMsg });

    const llmResponse = await axios.post(
      `${llmEndpoint}/api/chat`,
      {
        model: AI_MODEL,
        messages,
        max_tokens: 80,
        temperature: 0.8,
        top_p: 0.5,
      },
      { headers: { "Content-Type": "application/json" } }
    );

    const reply: string =
      llmResponse.data?.message?.content ?? "No response.";

    messages.push({ role: "assistant", content: reply });
    saveHistory(messages);

    const audioBuffer = await callChatterboxTTS(reply, "Sample_Voice.mpeg");
    const audioBase64 = audioBuffer.toString("base64");

    return withCors(
      NextResponse.json({
        response: reply,
        audioBase64,
        audioMime: "audio/mpeg",
      })
    );
  } catch (err) {
    const error = err as Error;
    return withCors(
      NextResponse.json(
        { error: "Internal server error", details: error.message },
        { status: 500 }
      )
    );
  }
}
