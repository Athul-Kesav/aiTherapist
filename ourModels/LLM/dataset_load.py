from datasets import load_dataset

# Define your JSONL files
data_files = {
    "train": "train.jsonl",
    "validation": "val.jsonl",
    "test": "test.jsonl"
}

# Load dataset directly from JSONL files
dataset = load_dataset("json", data_files=data_files)

print("✅ Dataset loaded successfully!")
print(dataset)
print("Columns:", dataset["train"].column_names)
print("Example:", dataset["train"][0])

# Save it to disk so train_lora.py can use it
dataset.save_to_disk("merged_dataset")

print("\n💾 Dataset saved to ./merged_dataset")
