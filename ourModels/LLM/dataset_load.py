from datasets import load_dataset

# Load each split from its JSON file
data_files = {
    "train": "train.jsonl",
    "validation": "val.jsonl",
    "test": "test.jsonl"
}

dataset = load_dataset("json", data_files=data_files)

# Show info
print("✅ Dataset loaded successfully!")
print(dataset)
print("Columns:", dataset["train"].column_names)
print("Example:", dataset["train"][0])

# Save to disk (so your train_lora.py can use it)
dataset.save_to_disk("merged_dataset")

print("\n💾 Dataset saved to ./merged_dataset")
