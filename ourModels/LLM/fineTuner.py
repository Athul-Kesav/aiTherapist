import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# Set the CUDA allocation configuration to avoid fragmentation
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import json
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer
)
import torch
torch.cuda.empty_cache()

# ---------------------------
# 1. Load the Formatted Dataset
# ---------------------------
dataset = load_dataset("json", data_files={"train": "formatted_dataset.jsonl"})

"""
    The dataset is of the format:
    {
        "Messages": 
        [
            {
                "Role": "user",
                "Content": "I just took a job that requires me to travel far away from home. My family and I...."
            },
            {
                "Role": "assistant",
                "Content": "hmm this is a tough one! I think...."
            }
        ]
    }

"""

# ---------------------------
# 2. Load the Tokenizer
# ---------------------------
base_model = "mistralai/Mistral-7B-v0.1"
tokenizer = AutoTokenizer.from_pretrained(base_model)
tokenizer.pad_token = tokenizer.eos_token

# ---------------------------
# 3. Define a Tokenization Function for Multi-Turn Conversations
# ---------------------------
def format_conversation(example):
    """
    Convert a multi-turn conversation (with a "Messages" array)
    into a single string formatted for fine-tuning.
    This function concatenates user messages wrapped in [INST] ... [/INST]
    followed by the assistant messages, and appends an end-of-sequence token.
    It also attaches labels (same as input_ids) for computing the loss.
    """
    conversation = ""
    for msg in example["Messages"]:
        if msg["Role"] == "user":
            conversation += "[INST] " + msg["Content"].strip() + " [/INST] "
        elif msg["Role"] == "assistant":
            conversation += msg["Content"].strip() + " "
    conversation += "</s>"  # End-of-sequence marker

   
    tokenized = tokenizer(
        conversation,
        truncation=True,
        padding="max_length",
        max_length=512  # Is this max_length relevant to the issue I'm facing ?
    )

    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

# Apply the tokenization function to the dataset
tokenized_dataset = dataset.map(format_conversation, batched=False)

# ---------------------------
# 4. Load the Mistral-7B Model with 4-bit Quantization and Attach LoRA Adapters
# ---------------------------
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)

model = AutoModelForCausalLM.from_pretrained(
    base_model,
    quantization_config=bnb_config,
    torch_dtype=torch.bfloat16,
    device_map={"": 0},
)

model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=32,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# ---------------------------
# 5. Set Up Training Arguments
# ---------------------------
training_args = TrainingArguments(
    output_dir="./mistral_finetuned",
    eval_strategy="no",  # Disable evaluation if no eval dataset is provided
    learning_rate=2e-5,
    per_device_train_batch_size=1,  # Lowered batch size
    gradient_accumulation_steps=4,  # Simulate a larger effective batch size
    num_train_epochs=3,
    weight_decay=0.01,
    fp16=True,
    logging_steps=50,
    save_total_limit=2,
    report_to="none",
)

# ---------------------------
# 6. Initialize the Trainer
# ---------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
)

# ---------------------------
# 7. Fine-Tune the Model
# ---------------------------
trainer.train()

# ---------------------------
# 8. Save the Fine-Tuned Model and Tokenizer
# ---------------------------
model.save_pretrained("./mistral_finetuned")
tokenizer.save_pretrained("./mistral_finetuned")

print("Fine-tuning complete and model saved in './mistral_finetuned'.")
