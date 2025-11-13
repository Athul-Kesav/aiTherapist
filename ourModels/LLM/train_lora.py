# LLM/train_lora.py
"""
Fine-tune a causal LM with LoRA (QLoRA-compatible).
Usage (example):
    accelerate launch LLM/train_lora.py -- --model_id meta-llama/Llama-3.2-3b --dataset_path /home/empathise/merged_dataset
Notes:
 - The script cleans dataset fields, flattens lists to text, ensures padding/truncation,
   and filters out invalid examples to prevent tensor creation errors.
 - It saves LoRA adapters and tokenizer to --output_dir at the end.
"""

import os
import argparse
import torch
import logging
from datasets import load_from_disk
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Reduce tokenizer parallelism warnings in forked processes
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
logging.basicConfig(level=logging.INFO)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model_id", type=str, default="meta-llama/Llama-3.2-3b")
    p.add_argument("--dataset_path", type=str, default="./merged_dataset")
    p.add_argument("--output_dir", type=str, default="./LLM/finetuned_lora")
    p.add_argument("--per_device_batch_size", type=int, default=2)
    p.add_argument("--gradient_accumulation_steps", type=int, default=8)
    p.add_argument("--num_train_epochs", type=int, default=2)
    p.add_argument("--max_length", type=int, default=512)
    p.add_argument("--learning_rate", type=float, default=2e-4)
    p.add_argument("--lora_r", type=int, default=16)
    p.add_argument("--lora_alpha", type=int, default=32)
    p.add_argument("--logging_steps", type=int, default=50)
    p.add_argument("--save_steps", type=int, default=500)
    p.add_argument("--use_4bit", action="store_true", help="Enable 4-bit quantization")
    return p.parse_args()


def clean_text_field(value):
    """
    Ensure the dataset field becomes a single string.
    If value is a list, join by space. If None, return empty string.
    """
    if value is None:
        return ""
    if isinstance(value, list):
        # flatten nested lists and convert each element to string
        flat = []
        for el in value:
            if isinstance(el, list):
                flat.extend([str(x) for x in el])
            else:
                flat.append(str(el))
        return " ".join(flat).strip()
    return str(value).strip()


def make_prompt(instruction, response):
    """
    Build the prompt used for causal LM training.
    Customize the template if you want a different format.
    """
    instruction = instruction.strip()
    response = response.strip()
    # Combined single text with instruction + response
    # We keep both so model sees the full example; for causal LM we feed full text as single string.
    return f"User: {instruction}\nAssistant: {response}"


def main():
    args = parse_args()

    print("🔹 Loading dataset from:", args.dataset_path)
    ds = load_from_disk(args.dataset_path)
    dataset = ds["train"] if "train" in ds else ds

    # quick sanity: show columns and a sample
    print("Dataset columns:", dataset.column_names)
    try:
        print("Example sample (raw):", dataset[0])
    except Exception:
        pass

    print("🔹 Loading tokenizer:", args.model_id)
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, use_fast=False)
    # ensure pad token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # set model max length defensively
    try:
        tokenizer.model_max_length = min(int(tokenizer.model_max_length), args.max_length)
    except Exception:
        tokenizer.model_max_length = args.max_length

    # ---------- Format (clean) dataset ----------
    def format_and_clean(example):
        # fetch potential fields in order of precedence
        instr = example.get("instruction") or example.get("prompt") or example.get("text") or ""
        resp = example.get("response") or example.get("completion") or ""
        instr = clean_text_field(instr)
        resp = clean_text_field(resp)
        full = make_prompt(instr, resp)
        return {"text": full, "raw_instruction": instr, "raw_response": resp}

    print("🔹 Formatting + cleaning dataset...")
    # remove non-essential columns safely (keep only minimal to avoid dropping unexpected fields)
    remove_cols = [c for c in dataset.column_names if c not in ["instruction", "response", "prompt", "text", "completion"]]
    dataset = dataset.map(format_and_clean, remove_columns=remove_cols, batched=False)

    # Filter out empty or invalid text entries
    def not_empty(example):
        t = example.get("text") or ""
        return isinstance(t, str) and len(t.strip()) > 0

    dataset = dataset.filter(not_empty)
    print(f"🔹 After cleaning, dataset size = {len(dataset)}")

    # ---------- Tokenize ----------
    def tokenize_batch(examples):
        # examples["text"] is a list of strings
        texts = examples["text"]
        # defensive: convert any non-strings to string, join lists if found
        processed = [clean_text_field(t) for t in texts]
        # tokenizer returns dict of lists (input_ids, attention_mask)
        out = tokenizer(
            processed,
            truncation=True,
            padding="max_length",  # Important: produces fixed-length lists for batching
            max_length=args.max_length,
            return_attention_mask=True,
            return_tensors=None,  # keep as python lists so datasets stores them
        )
        return out

    print("🔹 Tokenizing dataset (this may take a while)...")
    # keep original columns removed (we used 'text'); now remove 'text' after tokenization
    dataset = dataset.map(tokenize_batch, batched=True, remove_columns=["text", "raw_instruction", "raw_response"])

    # final filter: ensure input_ids exist and are lists of ints
    def valid_inputs(example):
        ids = example.get("input_ids")
        if ids is None:
            return False
        # ensure it's a non-empty list of ints
        if not isinstance(ids, list) or len(ids) == 0:
            return False
        return all(isinstance(x, int) for x in ids)

    dataset = dataset.filter(valid_inputs)
    print(f"🔹 After tokenization & validation, dataset size = {len(dataset)}")

    # Small debug: print one tokenized sample shapes
    try:
        sample = dataset[0]
        print("Sample keys:", sample.keys())
        print("Sample input_ids length:", len(sample["input_ids"]))
    except Exception:
        pass

    # ---------- Load model ----------
    print("🔹 Loading model:", args.model_id)
    if args.use_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        try:
            model = AutoModelForCausalLM.from_pretrained(
                args.model_id,
                load_in_8bit=True,
                device_map="auto",
                trust_remote_code=True,
            )
        except Exception:
            model = AutoModelForCausalLM.from_pretrained(
                args.model_id, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
            )

    # ---------- Prepare for k-bit (optional) ----------
    try:
        model = prepare_model_for_kbit_training(model)
    except Exception as e:
        print("⚠️ Warning: prepare_model_for_kbit_training failed, continuing:", e)

    # ---------- LoRA config ----------
    target_modules = ["q_proj", "v_proj"]
    model_module_names = [name for name, _ in model.named_modules()]
    available_targets = [m for m in target_modules if any(m in name for name in model_module_names)]
    if not available_targets:
        # fallback: choose commonly present linear-like layers
        fallback = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "down_proj", "up_proj"]
        available_targets = [t for t in fallback if any(t in name for name in model_module_names)][:2]

    print("🔹 Using LoRA target modules:", available_targets)
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=available_targets,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)

    # ---------- Training args ----------
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.per_device_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.num_train_epochs,
        learning_rate=args.learning_rate,
        fp16=True,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=2,
        remove_unused_columns=False,  # we already tokenized everything
        report_to="none",
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    # ---------- Trainer ----------
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # ---------- Train ----------
    print("🚀 Starting training (debug: first few batches)...")
    try:
        trainer.train()
    except Exception as e:
        # Helpful debug info in case of crash
        print("‼️ Training failed with exception:", e)
        # print a few problematic samples to debug
        for i in range(min(5, len(dataset))):
            print(f"--- sample {i} ---")
            s = dataset[i]
            # show first 20 tokens for sample
            print("input_ids[:20]:", s.get("input_ids")[:20] if s.get("input_ids") else None)
        raise

    # ---------- Save LoRA adapters & tokenizer ----------
    print("💾 Saving LoRA adapters to:", args.output_dir)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("✅ Training complete!")


if __name__ == "__main__":
    main()
