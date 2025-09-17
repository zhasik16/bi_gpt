import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("7474531664:AAEUBziUq4OivyF5jbRuPDi6arfIkkDGNK4")  # токен телеграм-бота
API_URL = os.getenv("API_URL", "http://localhost:8000/ask")  # твой backend API
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")  # где хостится фронт
