# infer_sql.py
import os, sqlite3
from transformers import T5ForConditionalGeneration, T5TokenizerFast

MODEL_DIR = "out_t5_spider/final"
SPIDER_DIR = "data/spider"

tokenizer = T5TokenizerFast.from_pretrained(MODEL_DIR)
model = T5ForConditionalGeneration.from_pretrained(MODEL_DIR).eval()

def build_schema_string(db_id):
    import json
    tables = json.load(open(os.path.join(SPIDER_DIR, "tables.json"), "r", encoding="utf-8"))
    meta = next(m for m in tables if m["db_id"] == db_id)
    tbls = meta["table_names_original"]
    cols = {}
    for (tbl_idx, col_name), col_type in zip(meta["column_names_original"], meta["column_types"]):
        if tbl_idx == -1: continue
        cols.setdefault(tbl_idx, []).append(f"{col_name}:{col_type}")
    serial = " | ".join(f"{tbls[i]}({', '.join(cols.get(i, []))})" for i in range(len(tbls)))
    return serial

def generate_sql(question, db_id, max_new_tokens=196):
    schema = build_schema_string(db_id)
    inp = f"translate to SQL | db: {db_id} | schema: {schema} | question: {question}"
    tok = tokenizer(inp, return_tensors="pt", truncation=True, max_length=1024)
    out = model.generate(**tok, max_new_tokens=max_new_tokens, num_beams=4, early_stopping=True)
    sql = tokenizer.decode(out[0], skip_special_tokens=True).strip()
    return sql

def is_safe_select(sql: str) -> bool:
    s = sql.strip().lower().replace("\n"," ")
    if not s.startswith("select"):
        return False
    bad = ["insert", "update", "delete", "drop", "alter", "truncate", "attach", "detach", ";"]
    return not any(b in s for b in bad)

def execute_sql(sql: str, db_id: str):
    db_path = os.path.join(SPIDER_DIR, "database", db_id, f"{db_id}.sqlite")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description] if cur.description else []
    con.close()
    return cols, rows

if __name__ == "__main__":
    q = "How many students are there in total?"
    db = "student_assessment"  # пример; подставь реальный db_id из dev
    sql = generate_sql(q, db)
    print("SQL:", sql)
    if is_safe_select(sql):
        cols, rows = execute_sql(sql, db)
        print(cols)
        print(rows[:5])
    else:
        print("Blocked non-SELECT or unsafe SQL")
