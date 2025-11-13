"""
Fine-tune a causal LM with LoRA (QLoRA-compatible).
Usage:
    accelerate launch LLM/train_lora.py -- --model_id meta-llama/Llama-3.2-3b
"""

import os
import argparse
import torch
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
    p.add_argument("--use_4bit", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()

    print("🔹 Loading dataset from:", args.dataset_path)
    ds = load_from_disk(args.dataset_path)
    dataset = ds["train"] if "train" in ds else ds

    print("🔹 Loading tokenizer:", args.model_id)
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, use_fast=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # --- STEP 1: Format dataset ---
    def format_example(ex):
        instr = ex.get("instruction") or ex.get("prompt") or ex.get("text") or ""
        resp = ex.get("response") or ex.get("completion") or ""
        instr, resp = str(instr).strip(), str(resp).strip()
        if not instr and not resp:
            return None
        return {"text": f"User: {instr}\nAssistant: {resp}".strip()}

    print("🔹 Formatting dataset...")
    dataset = dataset.map(format_example)
    dataset = dataset.filter(lambda x: x is not None and "text" in x and len(x["text"].strip()) > 0)

    # --- STEP 2: Tokenization ---
    def tokenize_fn(examples):
        valid_texts = [t for t in examples["text"] if isinstance(t, str) and len(t.strip()) > 0]
        return tokenizer(
            valid_texts,
            truncation=True,
            padding="max_length",
            max_length=args.max_length,
        )

    print("🔹 Tokenizing dataset...")
    dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])
    dataset = dataset.filter(lambda x: x.get("input_ids") is not None)

    # --- STEP 3: Load model ---
    print("🔹 Loading model:", args.model_id)
    if args.use_4bit:
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
        try:
            model = AutoModelForCausalLM.from_pretrained(
                args.model_id,
                load_in_8bit=True,
                device_map="auto",
                trust_remote_code=True
            )
        except Exception:
            model = AutoModelForCausalLM.from_pretrained(
                args.model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )

    # --- STEP 4: Prepare model for LoRA ---
    try:
        model = prepare_model_for_kbit_training(model)
    except Exception as e:
        print("⚠️ prepare_model_for_kbit_training failed, continuing:", e)

    # Pick target LoRA modules dynamically
    target_modules = ["q_proj", "v_proj"]
    names = [name for name, _ in model.named_modules()]
    available = [m for m in target_modules if any(m in name for name in names)]
    if not available:
        available = ["q_proj", "k_proj"]

    print("🔹 Using LoRA target modules:", available)
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=available,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)

    # --- STEP 5: Training setup ---
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
        remove_unused_columns=False,
        report_to="none",
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    # --- STEP 6: Trainer ---
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # --- STEP 7: Train ---
    print("🚀 Starting training...")
    trainer.train()

    # --- STEP 8: Save ---
    print("💾 Saving model to:", args.output_dir)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("✅ Training complete!")


if __name__ == "__main__":
    main()
