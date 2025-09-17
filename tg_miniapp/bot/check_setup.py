import os
from transformers import T5ForConditionalGeneration, T5TokenizerFast
import telebot

# Проверяем токен
try:
    TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    print("✅ Telegram token найден")
except KeyError:
    print("❌ TELEGRAM_BOT_TOKEN не задан!")

# Проверяем SQL_MODEL_DIR
MODEL_DIR = os.environ.get("SQL_MODEL_DIR", "out_t5_spider/final")
if os.path.exists(MODEL_DIR):
    print(f"✅ Модель T5 найдена в {MODEL_DIR}")
else:
    print(f"❌ Модель T5 не найдена по пути {MODEL_DIR}")

# Пробуем инициализировать бот
try:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    print("✅ Бот инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации бота: {e}")

# Пробуем инициализировать модель T5
try:
    tokenizer = T5TokenizerFast.from_pretrained(MODEL_DIR)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_DIR)
    print("✅ T5 модель и токенайзер загружены")
except Exception as e:
    print(f"❌ Ошибка загрузки модели: {e}")
