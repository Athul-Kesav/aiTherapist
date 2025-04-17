from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

import os

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch

# Load the tokenizer and model from the saved directory
model_dir = "./mistral_finetuned_2"
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForCausalLM.from_pretrained(model_dir)

# Create text generation pipeline
text_gen = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=3,
    max_length=300  # !! This is where the issue is
)

system_prompt = "[SYSTEM] You are a friendly empathetic therapist who likes helping people get over mental issues. Keep the conversations short and calming, to the point. You also retain therapeutic knowledge from past training. You let the user take their time, not ask direct questions, but ask the user when they are ready to talk. Be kind, sympathetic and empathetic.\n"
user_prompt = """[INST]The user is in a sad  mood.

The voice analysis is:
      - Max Pitch: 600
      - Min Pitch: 100
      - Average Intensity: 1.3
      - Sentiment Analysis: 
          - Label: Sad
          - Score: 85.465165
      - Transcript: I feel really low.

      Generate a human-like response to the user's mood.
      Do not use any offensive language.
      Make it sound like a conversation.
      If the question is unclear or vague, tell the user to provide more context.[/INST]"""
prompt = system_prompt + user_prompt

# Increase max_new_tokens for a more complete response
output = text_gen(
    prompt,
    do_sample=True,
    top_p=0.95,
    temperature=0.7,
    truncation=True,
)

generated_text = output[0]['generated_text']

# Remove the prompt portion by splitting at the closing [/INST] tag
if "[/INST]" in generated_text:
    response = generated_text.split("[/INST]")[-1].strip()
else:
    response = generated_text.strip()

print("\n\nResponse:", response)
