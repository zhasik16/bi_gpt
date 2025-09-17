from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo
from aiogram.utils import executor
import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    webapp_btn = types.KeyboardButton(
        text="Открыть BI-GPT",
        web_app=WebAppInfo(url=config.WEBAPP_URL)
    )
    kb.add(webapp_btn)

    await message.answer("Привет! Это BI-GPT миниаппа. Жми кнопку ниже 👇", reply_markup=kb)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
