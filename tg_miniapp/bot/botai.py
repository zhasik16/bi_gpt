import os, uuid, tempfile, subprocess, sqlite3, json, telebot
from faster_whisper import WhisperModel
from transformers import T5ForConditionalGeneration, T5TokenizerFast

# ===================== CONFIG =====================

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

SPIDER_DIR = os.environ.get("SPIDER_DIR", r"data/spider")
MODEL_DIR  = os.environ.get("SQL_MODEL_DIR", r"out_t5_spider/final")  # <- положи сюда свои веса (fine-tuned)

# Whisper конфиг
WHISPER_MODEL   = os.environ.get("WHISPER_MODEL", "small")
HAS_CUDA        = bool(os.environ.get("CUDA_VISIBLE_DEVICES"))
WHISPER_DEVICE  = "cuda" if HAS_CUDA else "cpu"
WHISPER_COMPUTE = os.environ.get("WHISPER_COMPUTE_TYPE") or ("float16" if HAS_CUDA else "int8")
CPU_THREADS     = int(os.environ.get("WHISPER_CPU_THREADS", max(1, (os.cpu_count() or 4)//2)))

# Ответы ограничим
MAX_ROWS = int(os.environ.get("MAX_ROWS", 20))
MAX_SQL_TOKENS = int(os.environ.get("MAX_SQL_TOKENS", 196))
    
# ================== INIT MODELS ===================
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

# faster-whisper (офлайн)
asr = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE, cpu_threads=CPU_THREADS)

# T5 токенайзер/модель (для старта можно подставить "google/t5-small")
tokenizer = T5TokenizerFast.from_pretrained(MODEL_DIR)
sql_model = T5ForConditionalGeneration.from_pretrained(MODEL_DIR).eval()

# ================== STATE: user -> db_id ==========
# простая in-memory карта (на прод лучше KV/БД)
USER_DB = {}

# ================ SPIDER helpers ==================
def load_tables():
    with open(os.path.join(SPIDER_DIR, "tables.json"), "r", encoding="utf-8") as f:
        return json.load(f)

TABLE_META = load_tables()
META_BY_DB = {m["db_id"]: m for m in TABLE_META}

def schema_string(db_id: str) -> str:
    m = META_BY_DB[db_id]
    tbls = m["table_names_original"]
    cols = {}
    for (tbl_idx, col_name), col_type in zip(m["column_names_original"], m["column_types"]):
        if tbl_idx == -1:
            continue
        cols.setdefault(tbl_idx, []).append(f"{col_name}:{col_type}")
    serial = " | ".join(f"{tbls[i]}({', '.join(cols.get(i, []))})" for i in range(len(tbls)))
    return serial

def db_path(db_id: str) -> str:
    return os.path.join(SPIDER_DIR, "database", db_id, f"{db_id}.sqlite")

# ================ Audio helpers ===================
def ogg_to_wav(in_path: str) -> str:
    out_path = in_path.rsplit(".", 1)[0] + ".wav"
    ffmpeg_bin = os.environ.get("FFMPEG_BIN", "ffmpeg")
    subprocess.run([ffmpeg_bin, "-y", "-i", in_path, "-ac","1","-ar","16000","-vn", out_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path

def transcribe(path: str, language="ru") -> str:
    segments, info = asr.transcribe(
        path, language=language, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        beam_size=1, best_of=1, temperature=0.0, no_speech_threshold=0.6,
        condition_on_previous_text=True
    )
    return " ".join(s.text for s in segments).strip()

# ================ NL -> SQL =======================
def build_input(question: str, db_id: str) -> str:
    sch = schema_string(db_id)
    return f"translate to SQL | db: {db_id} | schema: {sch} | question: {question}"

def generate_sql(question: str, db_id: str) -> str:
    inp = build_input(question, db_id)
    tok = tokenizer(inp, return_tensors="pt", truncation=True, max_length=1024)
    out = sql_model.generate(**tok, max_new_tokens=MAX_SQL_TOKENS, num_beams=4, early_stopping=True)
    sql = tokenizer.decode(out[0], skip_special_tokens=True).strip()
    return sql

def is_safe_select(sql: str) -> bool:
    s = sql.strip().lower().replace("\n", " ")
    if not s.startswith("select"):
        return False
    bad = ["insert", "update", "delete", "drop", "alter", "truncate", "attach", "detach", "create", "replace"]
    if any(b in s for b in bad): return False
    if ";" in s: return False
    return True

def execute_sql(sql: str, db_id: str):
    path = db_path(db_id)
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute(sql)
    rows = cur.fetchmany(MAX_ROWS + 1)  # +1 чтобы понять, что есть ещё
    cols = [d[0] for d in cur.description] if cur.description else []
    con.close()
    more = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    return cols, rows, more

def render_table(cols, rows, more=False) -> str:
    if not cols:
        return "Пустой ответ."
    # простой моноширинный рендер
    col_line = " | ".join(cols)
    sep = "-+-".join("-"*len(c) for c in cols)
    lines = [f"<code>{col_line}</code>", f"<code>{sep}</code>"]
    for r in rows:
        lines.append("<code>" + " | ".join(str(x) for x in r) + "</code>")
    if more:
        lines.append(f"\n<i>Показаны первые {MAX_ROWS} строк.</i>")
    return "\n".join(lines)

# ================= BOT COMMANDS ===================
@bot.message_handler(commands=["start", "help"])
def help_cmd(m):
    bot.reply_to(m,
        "Привет! Я голос→SQL бот.\n\n"
        "1) /db &lt;db_id&gt; — выбрать базу Spider\n"
        "2) пришли voice/audio с вопросом — я распознаю и выполню запрос\n"
        "3) /ask &lt;вопрос&gt; — текстовый вопрос без голоса\n\n"
        f"Spider dir: <code>{SPIDER_DIR}</code>\nModel dir: <code>{MODEL_DIR}</code>"
    )

@bot.message_handler(commands=["db"])
def set_db(m):
    parts = m.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(m, "Использование: /db &lt;db_id&gt;")
        return
    db_id = parts[1].strip()
    if db_id not in META_BY_DB:
        # подсказка по доступным
        sample = ", ".join(list(META_BY_DB.keys())[:10])
        bot.reply_to(m, f"Не знаю db_id <b>{db_id}</b>. Примеры: {sample} …")
        return
    USER_DB[m.chat.id] = db_id
    bot.reply_to(m, f"Ок, выбран db: <b>{db_id}</b>")

@bot.message_handler(commands=["health"])
def health(m):
    bot.reply_to(m, f"OK ✅\nASR: {WHISPER_MODEL} ({WHISPER_DEVICE}/{WHISPER_COMPUTE}, threads={CPU_THREADS})\nSQL model: {MODEL_DIR}")

@bot.message_handler(commands=["ask"])
def ask_cmd(m):
    db_id = USER_DB.get(m.chat.id)
    if not db_id:
        bot.reply_to(m, "Сначала выбери БД: /db &lt;db_id&gt;")
        return
    q = m.text.replace("/ask", "", 1).strip()
    if not q:
        bot.reply_to(m, "Использование: /ask &lt;вопрос&gt;")
        return
    try:
        sql = generate_sql(q, db_id)
        if not is_safe_select(sql):
            bot.reply_to(m, f"🚫 Небезопасный SQL:\n<code>{sql}</code>")
            return
        cols, rows, more = execute_sql(sql, db_id)
        bot.reply_to(m, f"<b>SQL:</b> <code>{sql}</code>\n\n{render_table(cols, rows, more)}")
    except Exception as e:
        bot.reply_to(m, f"Ошибка SQL: <code>{e}</code>")

@bot.message_handler(content_types=["voice","audio","video_note"])
def handle_voice(m):
    db_id = USER_DB.get(m.chat.id)
    if not db_id:
        bot.reply_to(m, "Сначала выбери БД: /db &lt;db_id&gt;")
        return
    try:
        file_id = (m.voice or m.audio or m.video_note).file_id
        info = bot.get_file(file_id)
        data = bot.download_file(info.file_path)
        with tempfile.TemporaryDirectory() as td:
            ogg_path = os.path.join(td, f"{uuid.uuid4()}.ogg")
            with open(ogg_path, "wb") as f:
                f.write(data)
            wav_path = ogg_to_wav(ogg_path)
            text = transcribe(wav_path, language="ru")  # фиксируем язык для скорости
        if not text:
            bot.reply_to(m, "Пустая транскрипция.")
            return
        # генерим и исполняем
        sql = generate_sql(text, db_id)
        if not is_safe_select(sql):
            bot.reply_to(m, f"<b>Распознано:</b> {text}\n\n🚫 Небезопасный SQL:\n<code>{sql}</code>")
            return
        cols, rows, more = execute_sql(sql, db_id)
        bot.reply_to(m, f"<b>Распознано:</b> {text}\n\n<b>SQL:</b> <code>{sql}</code>\n\n{render_table(cols, rows, more)}")
    except FileNotFoundError:
        bot.reply_to(m, "ffmpeg не найден. Укажи FFMPEG_BIN или добавь ffmpeg в PATH.")
    except Exception as e:
        bot.reply_to(m, f"Ошибка распознавания/SQL: <code>{e}</code>")

if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except Exception:
        pass
    print("Bot is up. Send /help")
    bot.infinity_polling(skip_pending=False, timeout=60, long_polling_timeout=60)
