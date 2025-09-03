import { NextResponse } from "next/server";

// import libraries
import axios from "axios";
import fs from "fs";
import path from "path";
import dotenv from "dotenv";

type CustomError = Error & {
  response?: { data?: unknown };
  config?: unknown;
};

const AI_MODEL = "llama3.2:latest"


// load .env variables
dotenv.config();

export async function OPTIONS() {
  const res = new NextResponse(null, { status: 200 });
  res.headers.set("Access-Control-Allow-Origin", "*");
  res.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
  return res;
}

function withCors(res: NextResponse) {
  res.headers.set("Access-Control-Allow-Origin", "*");
  res.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
  return res;
}



// 1. Point to context.txt in the same folder
const contextFilePath = path.join(process.cwd(), "app", "api", "analyze", "context.json");

export async function GET(): Promise<NextResponse> {

  return withCors(NextResponse.json({
      "message":"Hello from the Backend"
    }))
}

export async function POST(request: Request): Promise<NextResponse> {

  console.log("Backend Reached")

  const audioVideoEndpoint = process.env.AUDIO_VIDEO_ENDPOINT;
  const llmEndpoint = process.env.LLM_ENDPOINT;
  const MAX_CONTEXT_TOKENS = process.env.MAX_CONTEXT_TOKENS ? parseInt(process.env.MAX_CONTEXT_TOKENS) : 2048;

  function saveContext(context: number[]): void {
    // Ensure context does not exceed MAX_CONTEXT_TOKENS
    if (context.length > MAX_CONTEXT_TOKENS) {
      context = context.slice(-MAX_CONTEXT_TOKENS); // Keep only recent tokens
    }
    fs.writeFileSync(contextFilePath, JSON.stringify(context, null, 2), "utf-8");
  }

  function loadContext(): number[] {
    if (fs.existsSync(contextFilePath)) {
      const fileContent = fs.readFileSync(contextFilePath, "utf-8").trim();
      return fileContent ? JSON.parse(fileContent) as number[] : [];
    }
    return [];
  }


  let context: number[] = loadContext();

  console.log("Request received")

  // let llmResponse: { data: { response: string; context: number[] } } | null = null;
  try {
    // Parse the incoming form data
    const formData = await request.formData();
    const textPrompt = formData.get("textPrompt") as string;
    const fileField = formData.get("file");

    // If only text is provided
    if (!textPrompt) {
      if (!fileField) {
        return withCors(NextResponse.json(
          { error: "No video file provided." },
          { status: 400 }
        ))
      }
    } else {
      // If textPrompt is provided, append it to the context
      const llmResponse = await axios.post(`${llmEndpoint}`, {
        model: AI_MODEL,
        prompt: `${textPrompt}`,
        max_tokens: 50,
        temperature: 0.8,
        top_p: 0.5,
        stream: false,
        context: context,
      }, {
        headers: { "Content-Type": "application/json" }
      });

      if (llmResponse && llmResponse.data && llmResponse.data.context) {
        context = llmResponse.data.context;
      }

      saveContext(context);

      console.log("context saved")

      console.log("Response from LLM for text prompt sent")
      return withCors(NextResponse.json({
        "response": llmResponse?.data?.response || "No response available"
      }))

    }

    console.log("Accessing file field")
    // 'fileField' is a File object (browser/Web API), so convert it to a buffer.
    const videoFile = fileField as File;
    console.log("File field accessed")
    const arrayBuffer = await videoFile.arrayBuffer();
    const videoBuffer = Buffer.from(arrayBuffer);

    console.log("Sending data to other endpoints")

    // Prepare a FormData for the /analyze-audio endpoint.

    const audioVideoFormData = new FormData();
    audioVideoFormData.append("file", new Blob([videoBuffer], { type: videoFile.type }), videoFile.name);
    const audioVideoResponse = await fetch(`${audioVideoEndpoint}`, {
      method: "POST",
      body: audioVideoFormData,
    });

    const audioVideoData = await audioVideoResponse.json();

    const processorResponse = {
      message: "Video processed and sent successfully",
      audioVideoResponse: audioVideoData,
    }


    const promptText = `
      The user is in a ${processorResponse.audioVideoResponse?.face_emotion || "neutral"} mood.
      From the voice the emotion is - ${processorResponse.audioVideoResponse?.voice_emotion || "neutral"}

      - Transcript: "${processorResponse.audioVideoResponse?.transcription || "No transcript available"}"

      Generate a human-like response to the user's mood.
      Do not use any offensive language.
      Make it sound like a conversation.
      If the question is unclear or vague, tell the user to provide more context.
      `;

    console.log("Sending data to LLM")
    console.log(promptText)

    // Send the processed data to the LLM endpoint

    const llmResponse = await axios.post(
      `${llmEndpoint}`,
      {
        model: AI_MODEL,
        prompt: promptText,
        max_tokens: 50,
        temperature: 0.8,
        top_p: 0.5,
        stream: false,
        context: context
      },
      {
        headers: { "Content-Type": "application/json" }
      }
    );

    if (llmResponse && llmResponse.data && llmResponse.data.context) {
      context = llmResponse.data.context;
    }

    saveContext(context);

    console.log("context saved")

    console.log("Response sent to client")
    return withCors(NextResponse.json({
      "response": llmResponse?.data?.response || "No response available"
    }))

  } catch (error: unknown) {
    const e = error as CustomError;
    console.error("Error processing video:", {
      message: e.message,
      stack: e.stack,
      response: e.response?.data,
      config: e.config,
    });

    return withCors(NextResponse.json(
      { error: "Internal Server Error", details: e.message },
      { status: 500 }
    ))
  }

}
