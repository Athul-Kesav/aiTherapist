import { NextResponse } from "next/server";

import axios from "axios";

export async function POST(request: Request): Promise<NextResponse> {

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
    const audioResponse = await fetch("http://localhost:5000/analyze-audio", {
      method: "POST",
      body: audioFormData,
    });
    const audioData = await audioResponse.json();

    // Prepare a FormData for the /analyze-video endpoint.
    const videoFormData = new FormData();
    videoFormData.append("file", new Blob([videoBuffer], { type: videoFile.type }), videoFile.name);
    const videoResponse = await fetch("http://localhost:5000/analyze-video", {
      method: "POST",
      body: videoFormData,
    });
    const videoData = await videoResponse.json();


    const processorResponse = {
      message: "Video processed and sent successfully",
      audioResponse: audioData,
      videoResponse: videoData,
    }

    console.log(processorResponse)

    const response = await axios.post("http://localhost:11434/api/generate", {
      model:"mistral",
      prompt:`The user is in a ${processorResponse.videoResponse.mood} mood. The voice analysis is max_pitch : ${processorResponse.audioResponse.max_pitch}, min_pitch : ${processorResponse.audioResponse.min_pitch}, average_intensity : ${processorResponse.audioResponse.average_intensity}, transcript : ${processorResponse.audioResponse.transcript}, sentiment analysis : label - ${processorResponse.audioResponse.sentiment.label}, score - ${processorResponse.audioResponse.sentiment.score}.
      Generate a human-like response to the user's mood.`,
      max_tokens: 100,
      temperature: 0.9,
      top_p: 1,
      stream: false
    })

    console.log(response.data.response);

    return NextResponse.json({
      "response": response.data.response
    });
  } catch (error) {
    console.error("Error processing video:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
