import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

# -------------------------------
# 1️⃣ Dataset Loading
# -------------------------------
# Point to your 3 jsonl files
data_files = {
    "train": "LLM/train.jsonl",
    "validation": "LLM/val.jsonl",
    "test": "LLM/test.jsonl"
}

dataset = load_dataset("json", data_files=data_files)

# -------------------------------
# 2️⃣ Tokenizer + Model Setup
# -------------------------------
model_name = "microsoft/phi-2"   # or whichever model you used before

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # prevent padding issues

# quantization setup (replaces deprecated args)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)

# -------------------------------
# 3️⃣ LoRA configuration
# -------------------------------
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# -------------------------------
# 4️⃣ Tokenization
# -------------------------------
def preprocess_function(example):
    # Combine fields based on your dataset structure
    # Adjust keys if your dataset uses different names (like 'instruction', 'response', etc.)
    if "instruction" in example and "response" in example:
        text = f"Instruction: {example['instruction']}\nResponse: {example['response']}"
    elif "input" in example and "output" in example:
        text = f"Input: {example['input']}\nOutput: {example['output']}"
    else:
        # fallback if dataset has a single text field
        text = example.get("text", "")
    
    # Tokenize with truncation and padding
    return tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=512
    )

tokenized_datasets = dataset.map(preprocess_function, batched=False)

# -------------------------------
# 5️⃣ Data Collator + Training Args
# -------------------------------
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

training_args = TrainingArguments(
    output_dir="./lora_phi2_output",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-4,
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    logging_dir="./logs",
    logging_steps=50,
    save_total_limit=2,
    fp16=True,
    report_to="none"  # disable wandb etc
)

# -------------------------------
# 6️⃣ Trainer
# -------------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator
)

# -------------------------------
# 7️⃣ Train!
# -------------------------------
if __name__ == "__main__":
    print("🚀 Starting LoRA fine-tuning...")
    trainer.train()
    print("✅ Training complete! Saving model...")
    trainer.save_model("./lora_phi2_final")
