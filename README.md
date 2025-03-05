# EmpathAIse - An AI-Driven Mental Health Monitoring Software

EmpathAIse is a next-generation web application designed to support and monitor mental health by providing personalized, empathetic insights. By leveraging advanced AI models for video and audio analysis, EmpathAIse offers users a comprehensive picture of their mental state and delivers motivational, supportive messages tailored to their needs.

## Overview

EmpathAIse combines multiple state-of-the-art models to analyze a user's emotional well-being through both visual and auditory inputs. The core idea is to fuse data from several modalities—video for emotion detection and audio for pitch, intensity, and speech transcription—to create a holistic analysis of the user's mental state. The ultimate goal is to produce supportive feedback that not only informs the user about their current emotional condition but also provides comfort and motivation.

## Key Features

### Multimodal Data Analysis

Integrates both video and audio data to assess the user's emotional state, ensuring a more nuanced and accurate interpretation.

### Emotion Detection via Video

Utilizes a pretrained model from DeepFace to detect and classify facial emotions. There are plans to further improve accuracy by training a custom model using the AffectNet dataset.

### Audio Analysis

- Acoustic Feature Extraction:
Uses Librosa, a popular Python library, to extract pitch and intensity data from audio recordings.
- Speech Transcription:
Transcribes spoken words into text using an API service from AssemblyAI, adding a semantic layer to the analysis.

### Supportive AI Responses

The outputs from the emotion detection and audio analysis modules are designed to be fed into an AI-driven language model (LLM). This model will generate supportive, motivational, and friendly text responses that address the user's emotional state.

### Text-to-Speech Conversion

The generated text responses will be converted into speech, creating a more engaging and interactive experience for users.

### Planned Avatar Integration

Future iterations will incorporate an avatar that uses the final synthesized speech to display human-like expressions. This will help enhance the empathetic quality of the interaction, making the experience more personal and relatable.

## Technical Details

### Frontend

A responsive web interface that ensures accessibility and usability across devices, including desktops and mobile devices.

### Backend & AI Modules

- Video Processing:
Implements emotion detection using DeepFace with plans to evolve into a custom model trained on the AffectNet dataset.
- Audio Processing:
Uses Librosa for audio feature extraction and AssemblyAI for robust speech-to-text conversion.
- LLM Integration:
The next phase involves integrating an AI model to process the multimodal inputs and generate emotionally supportive responses.
- Responsive Design Considerations:
Special attention is given to mobile responsiveness, including dynamic viewport height adjustments to cater for mobile browser UI elements, ensuring a smooth, scroll-free user experience.
