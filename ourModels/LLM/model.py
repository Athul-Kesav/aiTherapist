from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

# Choose your model
model_name = "EleutherAI/gpt-neo-2.7B"

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Create a chat pipeline
chatbot = pipeline("text-generation", model=model, tokenizer=tokenizer)

def generate(prompt):
    response = chatbot(prompt, max_length=150, do_sample=True, temperature=0.7)
    return {"generated_text": response}

print(generate("Hello"))