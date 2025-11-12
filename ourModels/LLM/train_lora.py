# LLM/train_lora.py
"""
Fine-tune a causal LM with LoRA (QLoRA-compatible).
Assumes you already have:
 - a merged dataset saved with datasets.save_to_disk("merged_dataset")
 - a valid HF token (huggingface-cli login)
Usage:
    accelerate launch LLM/train_lora.py -- --model_id meta-llama/Llama-3.2-3b
"""

import os
import argparse
from functools import partial

import torch
from datasets import load_from_disk
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import BitsAndBytesConfig

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model_id", type=str, default="meta-llama/Llama-3.2-3b", help="HF model id to fine-tune")
    p.add_argument("--dataset_path", type=str, default="./merged_dataset", help="path to dataset saved with save_to_disk")
    p.add_argument("--output_dir", type=str, default="./LLM/finetuned_lora", help="where to store adapters and checkpoints")
    p.add_argument("--per_device_batch_size", type=int, default=2)
    p.add_argument("--gradient_accumulation_steps", type=int, default=8)
    p.add_argument("--num_train_epochs", type=int, default=2)
    p.add_argument("--max_length", type=int, default=512)
    p.add_argument("--learning_rate", type=float, default=2e-4)
    p.add_argument("--lora_r", type=int, default=16)
    p.add_argument("--lora_alpha", type=int, default=32)
    p.add_argument("--logging_steps", type=int, default=50)
    p.add_argument("--save_steps", type=int, default=500)
    p.add_argument("--use_4bit", action="store_true", help="Load model in 4-bit (requires bitsandbytes)")
    return p.parse_args()

def main():
    args = parse_args()

    # 1) Load dataset from disk (created by prepare_data.py)
    print("Loading dataset from:", args.dataset_path)
    ds = load_from_disk(args.dataset_path)
    # dataset should have columns: instruction, response
    if "train" in ds:
        dataset = ds["train"]
    else:
        dataset = ds  # if single dataset saved

    # 2) Tokenizer
    print("Loading tokenizer:", args.model_id)
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, use_fast=False)
    # ensure pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 3) Text -> prompt formatting
    def format_example(ex, max_length=args.max_length):
        # Expect dataset columns 'instruction' and 'response', else fallback
        instr = ex.get("instruction") or ex.get("prompt") or ex.get("text") or ""
        resp = ex.get("response") or ex.get("completion") or ""
        prompt = f"User: {instr}\nAssistant:"
        full = prompt + " " + resp
        return {"text": full}

    print("Formatting dataset...")
    dataset = dataset.map(format_example, remove_columns=[c for c in dataset.column_names if c not in ["instruction","response","text"]], batched=False)

    # 4) Tokenize
    def tokenize_fn(example):
        return tokenizer(example["text"], truncation=True, max_length=args.max_length, padding="max_length")

    print("Tokenizing...")
    dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

    # 5) Load model (optionally in 4-bit)
    print("Loading model:", args.model_id)
    bnb_config = None
    model_kwargs = {"trust_remote_code": True}
    if args.use_4bit:
        # BitsAndBytes 4-bit config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
    else:
        # try to load in 8-bit (bitsandbytes) if available, else FP16
        try:
            model = AutoModelForCausalLM.from_pretrained(
                args.model_id,
                load_in_8bit=True,
                device_map="auto",
                trust_remote_code=True
            )
        except Exception:
            model = AutoModelForCausalLM.from_pretrained(args.model_id, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True)

    # 6) Prepare for kbit training (if quantized)
    try:
        model = prepare_model_for_kbit_training(model)
    except Exception:
        # if prepare_model_for_kbit_training fails, continue — it's optional for non-kbit models
        pass

    # 7) LoRA config
    # common target modules for Llama-like models: "q_proj","v_proj" — we'll inspect if necessary
    target_modules = ["q_proj", "v_proj"]
    # fallback: detect modules present
    model_module_names = [name for name, _ in model.named_modules()]
    available_targets = [m for m in target_modules if any(t in name for name in model_module_names for t in [m])]
    if not available_targets:
        # fallback to common linear names
        available_targets = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "down_proj", "up_proj"]
        available_targets = [t for t in available_targets if any(t in name for name, _ in model.named_modules())][:2]

    print("Using LoRA target modules:", available_targets)
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=available_targets,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)

    # 8) TrainingArguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.per_device_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.num_train_epochs,
        learning_rate=args.learning_rate,
        fp16=True,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=3,
        remove_unused_columns=False,
        report_to="none"
    )

    # 9) Data collator
    data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    # 10) Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # 11) Train
    print("Starting training...")
    trainer.train()

    # 12) Save adapters
    print("Saving LoRA adapters to:", args.output_dir)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("Done.")

if __name__ == "__main__":
    main()
