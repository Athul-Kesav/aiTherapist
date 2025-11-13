#!/usr/bin/env python3
"""
train_lora.py — LoRA fine-tuning entrypoint for JSONL datasets.

Usage (on AI server with accelerate+GPU):
    accelerate launch train_lora.py

Notes:
- Place train.jsonl, val.jsonl, test.jsonl in the same folder where you run this script (LLM/).
- The script is robust to dataset fields named ('instruction','response') or ('input','output')
  or a single 'text' field. Adjust model_name if needed.
"""

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model

# -----------------------------
# Config (edit if you want)
# -----------------------------
# Use a model that you have access to on the server (change if needed).
# On the AI server you used meta-llama previously; change here as appropriate.
model_name = "meta-llama/Llama-3.2-3b"  # <- change if you want another HF id

# Tokenization / training hyperparameters
MAX_LENGTH = 512
PER_DEVICE_BATCH_SIZE = 2
GRAD_ACCUM = 8
NUM_EPOCHS = 2
LEARNING_RATE = 2e-4
OUTPUT_DIR = "./lora_finetuned"

# -----------------------------
# 1) Load JSONL dataset
# -----------------------------
# Paths are relative to the current working directory (LLM/)
data_files = {
    "train": "./train.jsonl",
    "validation": "./val.jsonl",
    "test": "./test.jsonl",
}

print("📥 Loading JSONL dataset from:", data_files)
dataset = load_dataset("json", data_files=data_files)
print("✔️ Loaded dataset:", dataset)

# -----------------------------
# 2) Tokenizer + Model (bnb optional)
# -----------------------------
print("🔁 Loading tokenizer:", model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
# ensure pad token exists (required for batching / data collator)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# BitsAndBytes config — used only if the environment supports it (CUDA).
# If you run on a machine without CUDA, this may error; use the non-quantized fallback.
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

print("🔁 Loading model with quantization_config (if supported):", model_name)
try:
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
except Exception as e:
    # Fallback when bitsandbytes / quantization is not available (e.g., local Mac)
    print("⚠️ Quantized load failed — falling back to float16 load:", e)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )

# -----------------------------
# 3) LoRA setup
# -----------------------------
# Typical target modules for Llama-like models are q_proj and v_proj.
# We pick those if available; PEFT will ignore modules not present.
target_modules = ["q_proj", "v_proj"]
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=target_modules,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
print("🔧 LoRA wrapped model (adapters ready)")

# -----------------------------
# 4) Preprocess & Tokenize (batched)
# -----------------------------
# Build prompts robustly from dataset fields. This function handles a batch of examples.
def build_prompts_and_tokenize(batch):
    """
    batch: dict of lists (datasets passes batched=True)
    We return the tokenized mapping (input_ids, attention_mask, etc.)
    """
    prompts = []
    # detect which keys exist in this dataset
    # note: sometimes dataset libraries return columns like 'instruction' or 'input'
    # handle common combos. fallback to 'text'.
    for i in range(len(next(iter(batch.values())))):  # length of batch
        # Try instruction/response
        instr = batch.get("instruction", [None] * len(next(iter(batch.values()))))[i]
        resp = batch.get("response", [None] * len(next(iter(batch.values()))))[i]

        # if not present, try input/output
        if instr is None and "input" in batch:
            instr = batch.get("input", [None])[i]
        if resp is None and "output" in batch:
            resp = batch.get("output", [None])[i]

        # fallback single text field
        if (instr is None or instr == "") and "text" in batch:
            instr = batch.get("text", [None])[i]

        # Normalize lists -> strings (if any entries are lists)
        if isinstance(instr, list):
            instr = " ".join(map(str, instr))
        if isinstance(resp, list):
            resp = " ".join(map(str, resp))

        # Coerce to strings safely
        instr = "" if instr is None else str(instr).strip()
        resp = "" if resp is None else str(resp).strip()

        # Build final prompt. If there's a response present, include it so model learns mapping.
        # If you want instruction-only SFT (i.e., model to predict response), you might structure differently.
        if instr and resp:
            prompt = f"User: {instr}\nAssistant: {resp}"
        elif instr:
            prompt = f"User: {instr}\nAssistant:"
        elif resp:
            prompt = f"Assistant: {resp}"
        else:
            prompt = ""

        prompts.append(prompt)

    # Tokenize the batch of prompts. Batched tokenizer avoids the NoneType tensor issues.
    tokenized = tokenizer(
        prompts,
        truncation=True,
        padding="max_length",  # ensures equal length tensors in a batch
        max_length=MAX_LENGTH,
    )
    return tokenized

print("🔤 Tokenizing dataset (batched)...")
# Use batched=True for efficiency and correct tokenizer inputs
# remove original columns to avoid collisions later
orig_columns = dataset["train"].column_names
tokenized_datasets = dataset.map(
    build_prompts_and_tokenize,
    batched=True,
    remove_columns=orig_columns,
)

print("✅ Tokenization done. Columns now:", tokenized_datasets["train"].column_names)

# Optional: filter out any samples that somehow ended up empty after preprocessing
def has_valid_input_ids(example):
    ids = example.get("input_ids", None)
    return ids is not None and isinstance(ids, list) and len(ids) > 0

tokenized_datasets["train"] = tokenized_datasets["train"].filter(has_valid_input_ids)
tokenized_datasets["validation"] = tokenized_datasets["validation"].filter(has_valid_input_ids)

# -----------------------------
# 5) Data collator + Training args
# -----------------------------
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=LEARNING_RATE,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    logging_dir="./logs",
    logging_steps=50,
    save_total_limit=2,
    fp16=True,
    report_to="none",
)

# -----------------------------
# 6) Trainer and train
# -----------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
)

if __name__ == "__main__":
    print("🚀 Starting training...")
    trainer.train()
    print("💾 Saving LoRA adapters and tokenizer to:", OUTPUT_DIR)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("✅ Done.")
