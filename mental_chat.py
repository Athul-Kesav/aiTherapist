import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftConfig, PeftModel
from flask import Flask, request, jsonify

app = Flask(__name__)

# Define model parameters
base_model = "mistralai/Mistral-7B-Instruct-v0.2"
adapter = "GRMenon/mental-health-mistral-7b-instructv0.2-finetuned-V2"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    base_model,
    add_bos_token=True,
    trust_remote_code=True,
    padding_side="left"
)

# Create PEFT model using base_model and finetuned adapter
peft_config = PeftConfig.from_pretrained(adapter)
# Load the base model without quantization
model = AutoModelForCausalLM.from_pretrained(
    peft_config.base_model_name_or_path,
    device_map="auto",
    torch_dtype=torch.float16  # or use torch.float32 if your GPU doesn't support FP16
)
model = PeftModel.from_pretrained(model, adapter)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "Hello!")
    messages = [{"role": "user", "content": user_message}]
    
    # Prepare input_ids using the model's chat template
    input_ids = tokenizer.apply_chat_template(
        conversation=messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(device)
    
    # Generate response
    output_ids = model.generate(
        input_ids=input_ids, max_new_tokens=512, do_sample=True, pad_token_id=2
    )
    response = tokenizer.batch_decode(
        output_ids.detach().cpu().numpy(), skip_special_tokens=True
    )
    
    return jsonify({"response": response[0]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
