from transformers import T5ForConditionalGeneration, T5TokenizerFast
import torch

MODEL_PATH = "out_t5_spider/final"

tokenizer = T5TokenizerFast.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH).to("cuda" if torch.cuda.is_available() else "cpu")

def ask(query, db_id="academic"):
    inp = f"{db_id} | {query}"
    inputs = tokenizer(inp, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_length=128)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

print(ask("List the names of all students.", db_id="course"))

