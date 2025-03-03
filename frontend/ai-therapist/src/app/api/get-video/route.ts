import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { Readable } from "stream";
import formidable, { File as FormidableFile, Fields, Files } from "formidable";
import type { IncomingMessage } from "http";

// Convert a Buffer into a Readable stream that yields the entire buffer as one chunk.
function bufferToStream(buffer: Buffer): Readable {
  return Readable.from([buffer]);
}

export async function POST(request: Request): Promise<NextResponse> {
  try {
    // 1. Retrieve the raw request body and the Content-Type header.
    const contentType: string = request.headers.get("content-type") || "";
    const rawBuffer: Buffer = Buffer.from(await request.arrayBuffer());
    const stream: Readable = bufferToStream(rawBuffer);

    // 2. Create a "fake" IncomingMessage with the required headers for formidable.
    const fakeReq = Object.assign(stream, {
      headers: { "content-type": contentType },
    }) as unknown as IncomingMessage;

    // 3. Parse the incoming multipart/form-data using formidable.
    const form = formidable({ multiples: false });
    const { fields, files }: { fields: Fields; files: Files } = await new Promise((resolve, reject) => {
      form.parse(fakeReq, (err, fields, files) => {
        if (err) reject(err);
        else resolve({ fields, files });
      });
    });

    // 4. Retrieve the video file from the parsed form (expected key: "file").
    const videoFile = files.file as FormidableFile | FormidableFile[];
    let uploadedFile: FormidableFile;
    if (Array.isArray(videoFile)) {
      uploadedFile = videoFile[0];
    } else {
      uploadedFile = videoFile;
    }

    if (!uploadedFile) {
      console.error("No video file provided at backend.");
      return NextResponse.json(
        { error: "No video file provided at backend." },
        { status: 400 }
      );
    }

    // 5. Create a temporary directory and define a file path.
    const tempDir: string = path.join(process.cwd(), "tmp");
    await fs.mkdir(tempDir, { recursive: true });
    const inputPath: string = path.join(tempDir, "input.webm");

    // 6. Save the uploaded file from formidable's temporary storage to our desired location.
    await fs.copyFile(uploadedFile.filepath, inputPath);

    // 7. Read the saved file into a buffer.
    const videoBuffer: Buffer = await fs.readFile(inputPath);

    // 8. Prepare a FormData for the /analyze-audio endpoint and send the video.
    const audioFormData = new FormData();
    audioFormData.append("file", new Blob([videoBuffer], { type: "video/webm" }), "video.webm");
    const audioResponse = await fetch("http://localhost:5000/analyze-audio", {
      method: "POST",
      body: audioFormData,
    });
    const audioData = await audioResponse.json();

    // 9. Prepare a separate FormData for the /analyze-video endpoint and send the video.
    const videoFormData = new FormData();
    videoFormData.append("file", new Blob([videoBuffer], { type: "video/webm" }), "video.webm");
    const videoResponse = await fetch("http://localhost:5000/analyze-video", {
      method: "POST",
      body: videoFormData,
    });
    const videoData = await videoResponse.json();

    // 10. Return a JSON response including the responses from both endpoints.
    return NextResponse.json({
      message: "Video processed and sent successfully",
      audioResponse: audioData,
      videoResponse: videoData,
    });
  } catch (error) {
    console.error("Error processing video:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
