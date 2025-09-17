# prep_spider.py
import json, os
from collections import defaultdict

SPIDER_DIR = "data/spider"

def load_tables():
    with open(os.path.join(SPIDER_DIR, "tables.json"), "r", encoding="utf-8") as f:
        tables = json.load(f)
    by_db = {}
    for t in tables:
        db = t["db_id"]
        cols = []
        for (tid, colname), (table_names) in zip(t["column_names"], t["table_names_original"]):
            pass
        # Соберём простой сериализатор
    by_db = {}
    with open(os.path.join(SPIDER_DIR, "tables.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)
    for m in meta:
        db_id = m["db_id"]
        tbls = m["table_names_original"]
        cols = defaultdict(list)
        for (tbl_idx, col_name), col_type in zip(m["column_names_original"], m["column_types"]):
            if tbl_idx == -1:  # * (звёздочка) — пропускаем
                continue
            cols[tbl_idx].append((col_name, col_type))
        serial = []
        for i, tname in enumerate(tbls):
            cc = ", ".join([f"{c}:{t}" for c, t in cols.get(i, [])])
            serial.append(f"{tname}({cc})")
        by_db[db_id] = " | ".join(serial)
    return by_db

def load_split(name):
    with open(os.path.join(SPIDER_DIR, f"{name}.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def make_pairs(split):
    by_db = load_tables()
    pairs = []
    for ex in load_split(split):
        q = ex["question"]
        sql = ex["query"]
        db = ex["db_id"]
        schema = by_db[db]
        inp = f"translate to SQL | db: {db} | schema: {schema} | question: {q}"
        tgt = sql
        pairs.append({"input": inp, "target": tgt, "db_id": db})
    return pairs

if __name__ == "__main__":
    train = make_pairs("train_spider")
    dev = make_pairs("dev")
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/train.jsonl", "w", encoding="utf-8") as f:
        for r in train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open("data/processed/dev.jsonl", "w", encoding="utf-8") as f:
        for r in dev:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("done")
