from transformers import AutoModelForCausalLM, AutoTokenizer  

model_id = "meta-llama/Llama-3.2-3b"  
tokenizer = AutoTokenizer.from_pretrained(model_id)  
model = AutoModelForCausalLM.from_pretrained(model_id, load_in_8bit=True, device_map="auto")
