import { NextRequest, NextResponse } from 'next/server';
import { Client } from "@gradio/client";

// Define the expected structure of the successful result from client.predict()
interface GradioPredictResult {
    data: (string | any)[];
}

// Define the expected structure of the error object sometimes thrown by Gradio client
interface GradioStatusError {
    type: 'status';
    stage: 'error';
    message: string | null;
    // other properties like endpoint, time, success, etc.
}

// Helper function to convert a File/Blob/Buffer to a Base64 Data URL string
async function fileToGradioBase64(file: File): Promise<string> {
    const buffer = Buffer.from(await file.arrayBuffer());
    // The mime type is important for Gradio to identify the file format
    return `data:${file.type};base64,${buffer.toString('base64')}`;
}

// Type guard to check if the error is the Gradio Status Error object
function isGradioStatusError(error: any): error is GradioStatusError {
    return (
        typeof error === 'object' &&
        error !== null &&
        'type' in error &&
        error.type === 'status' &&
        'stage' in error &&
        error.stage === 'error'
    );
}

export async function POST(request: NextRequest) {
    try {
        // 1. Parse the FormData from the incoming request
        const formData = await request.formData();
        const text_input = formData.get('text_input') as string;
        const audio_prompt_file = formData.get('audio_prompt_file') as File;

        if (!text_input || !audio_prompt_file) {
            return NextResponse.json({ error: 'Missing text input or audio prompt file.' }, { status: 400 });
        }

        // 2. Convert the uploaded audio file to the Base64 string format
        const base64Prompt = await fileToGradioBase64(audio_prompt_file);

        // 3. Connect to the Gradio Space dynamically
        const client = await Client.connect("ResembleAI/Chatterbox");

        // 4. Call the predict method using the exact API name
        const result = await client.predict("/generate_tts_audio", {
            text_input: text_input,            // 0. text_input (string)
            audio_prompt_path_input: base64Prompt, // 1. audio_prompt_path_input (Base64 string)
            exaggeration_input: 0.5,           // 2. exaggeration_input (number)
            temperature_input: 0.8,            // 3. temperature_input (number)
            seed_num_input: 0,                 // 4. seed_num_input (number)
            cfgw_input: 0.5,                   // 5. cfgw_input (number)
            vad_trim_input: false,             // 6. vad_trim_input (boolean)
        }) as GradioPredictResult;

        // The result structure from @gradio/client is { data: [output1, output2, ...], ... }
        const audioDataUrl = result?.data?.[0];

        if (audioDataUrl && typeof audioDataUrl === 'string' && audioDataUrl.startsWith('data:audio')) {
            return NextResponse.json({ audioDataUrl });
        } else {
            console.error('Gradio API did not return valid audio data URL. Full result:', result);
            return NextResponse.json({ error: 'Gradio API did not return valid audio data URL.' }, { status: 500 });
        }

    } catch (error) {
        // --- CORRECTED ERROR HANDLING BLOCK ---
        console.error('TTS API Error:', error);

        let clientMessage: string = 'Internal server error during TTS generation.';

        if (isGradioStatusError(error)) {
            // Handle the specific Gradio status error object where message might be null
            clientMessage = error.message
                ? `Gradio Error: ${error.message}`
                : 'The Gradio Space timed out or failed to process the request internally. Please try again.';
        } else if (error instanceof Error) {
            // Handle standard Error objects
            clientMessage = error.message;
        }

        // Include a clearer error message for the user, focusing on the high chance of timeout
        const userFriendlyMessage = clientMessage.includes('Could not connect') || clientMessage.includes('timed out')
            ? 'The remote voice model is currently busy or has failed (timeout). Please wait a minute and try generating a shorter text.'
            : clientMessage;

        return NextResponse.json({ error: userFriendlyMessage }, { status: 500 });
        // --- END CORRECTED ERROR HANDLING BLOCK ---
    }
}