import { NextResponse } from "next/server";

// import libraries
import axios from "axios";
import fs from "fs";
import path from "path";
import dotenv from "dotenv";

// load .env variables
dotenv.config();



// 1. Point to context.txt in the same folder
const contextFilePath = path.join(process.cwd(), "app", "api", "analyze", "context.json");


export async function POST(request: Request): Promise<NextResponse> {

  const audioEndpoint = process.env.AUDIO_ENDPOINT;
  const videoEndpoint = process.env.VIDEO_ENDPOINT;
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

  try {

    // Parse the incoming form data
    const formData = await request.formData();
    const fileField = formData.get("file");

    if (!fileField) {
      return NextResponse.json(
        { error: "No video file provided." },
        { status: 400 }
      );
    }

    // 'fileField' is a File object (browser/Web API), so convert it to a buffer.
    const videoFile = fileField as File;
    const arrayBuffer = await videoFile.arrayBuffer();
    const videoBuffer = Buffer.from(arrayBuffer);

    console.log("Sending data to other endpoints")

    // Prepare a FormData for the /analyze-audio endpoint.

    const audioFormData = new FormData();
    audioFormData.append("file", new Blob([videoBuffer], { type: videoFile.type }), videoFile.name);
    const audioResponse = await fetch(`${audioEndpoint}`, {
      method: "POST",
      body: audioFormData,
    });

    const audioData = await audioResponse.json();

    // Prepare a FormData for the /analyze-video endpoint.

    const videoFormData = new FormData();
    videoFormData.append("file", new Blob([videoBuffer], { type: videoFile.type }), videoFile.name);
    const videoResponse = await fetch(`${videoEndpoint}`, {
      method: "POST",
      body: videoFormData,
    });

    const videoData = await videoResponse.json();

    const processorResponse = {
      message: "Video processed and sent successfully",
      audioResponse: audioData,
      videoResponse: videoData,
    }

    
    const promptText = `
      The user is in a ${processorResponse.videoResponse?.mood || "neutral"} mood.
      The voice analysis is:
      - Max Pitch: ${processorResponse.audioResponse?.max_pitch || "unknown"}
      - Min Pitch: ${processorResponse.audioResponse?.min_pitch || "unknown"}
      - Average Intensity: ${processorResponse.audioResponse?.average_intensity || "unknown"}
      - Sentiment Analysis: 
          - Label: ${processorResponse.audioResponse?.sentiment?.label || "unknown"}
          - Score: ${processorResponse.audioResponse?.sentiment?.score || 0}
      - Transcript: "${processorResponse.audioResponse?.transcript || "No transcript available"}"

      Generate a human-like response to the user's mood.
      Do not use any offensive language.
      Make it sound like a conversation.
      If the question is unclear or vague, tell the user to provide more context.
      `;

    console.log("Sending data to LLM")
    console.log(promptText)
    
    // Send the processed data to the LLM endpoint

    const llmResponse = await axios.post(`${llmEndpoint}`, {
        model: "mistral",
        prompt: `${promptText}`,
        max_tokens: 200,
        temperature: 0.8,
        top_p: 0.5,
        stream: false,
        context: context
      }
    )

    context = llmResponse.data.context;

    saveContext(context);

    console.log("context saved")

    console.log("Response sent to client")
    return NextResponse.json({
      "response": llmResponse.data.response
    });

  } catch (error) {
    console.error("Error processing video:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
