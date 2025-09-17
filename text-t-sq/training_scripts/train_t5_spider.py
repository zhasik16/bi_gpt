# train_t5_spider.py (совместимый)
import os, torch
from datasets import load_dataset
from transformers import (
    T5ForConditionalGeneration, T5TokenizerFast,
    DataCollatorForSeq2Seq, Seq2SeqTrainingArguments, Seq2SeqTrainer
)
from peft import LoraConfig, get_peft_model

MODEL_NAME   = "t5-small"
TRAIN_PATH   = "data/processed/train.jsonl"
DEV_PATH     = "data/processed/dev.jsonl"
OUT_DIR      = "out_t5_spider"
MAX_INPUT    = 512
MAX_TARGET   = 128
EPOCHS       = 3

tokenizer = T5TokenizerFast.from_pretrained(MODEL_NAME)

def load_jsonl(path): return load_dataset("json", data_files=path, split="train")

def tok_fn(batch):
    m = tokenizer(batch["input"], max_length=MAX_INPUT, truncation=True)
    with tokenizer.as_target_tokenizer():
        lab = tokenizer(batch["target"], max_length=MAX_TARGET, truncation=True)
    m["labels"] = lab["input_ids"]
    return m

train_ds = load_jsonl(TRAIN_PATH)
dev_ds   = load_jsonl(DEV_PATH)

train_tok = train_ds.map(tok_fn, batched=True, remove_columns=train_ds.column_names)
dev_tok   = dev_ds.map(tok_fn,   batched=True, remove_columns=dev_ds.column_names)

# (опционально на быстрый тест)
# train_tok = train_tok.select(range(200))
# dev_tok   = dev_tok.select(range(50))

base = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
peft_cfg = LoraConfig(
    r=16, lora_alpha=32, target_modules=["q","v","k","o","wi","wo"],
    lora_dropout=0.05, bias="none", task_type="SEQ_2_SEQ_LM"
)
model = get_peft_model(base, peft_cfg)

torch.set_float32_matmul_precision("high")
use_bf16 = torch.cuda.is_available() and torch.cuda.get_device_capability(0)[0] >= 8
fp16_flag = not use_bf16

args = Seq2SeqTrainingArguments(
    output_dir=OUT_DIR,
    learning_rate=2e-4,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    gradient_accumulation_steps=2,
    num_train_epochs=EPOCHS,
    logging_steps=50,
    save_total_limit=2,
    save_steps=500,
    predict_with_generate=True,
    fp16=fp16_flag,
    bf16=use_bf16,
    dataloader_pin_memory=True,
    report_to="none",
    do_eval=True,                 # в старых версиях достаточно этого
)

data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

trainer = Seq2SeqTrainer(
    model=model,
    args=args,
    train_dataset=train_tok,
    eval_dataset=dev_tok,         # будет валидировать при save_steps (или по кнопке)
    data_collator=data_collator,
    tokenizer=tokenizer,
)

if __name__ == "__main__":
    trainer.train()
    # можно руками вызвать eval на dev:
    try:
        print(trainer.evaluate())
    except Exception as e:
        print("Eval skipped:", e)
    trainer.save_model(f"{OUT_DIR}/final")
    tokenizer.save_pretrained(f"{OUT_DIR}/final")
    print("✅ trained & saved")
