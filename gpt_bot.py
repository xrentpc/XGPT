import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# 🔐 Получаем токены из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔒 Проверка токенов
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN или OPENAI_API_KEY не заданы.")

# ⚙️ Настройка клиента OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# 🔇 Логирование
logging.basicConfig(level=logging.WARNING)

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ChatGPT-бот 🤖. Напиши мне что-нибудь.")

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        reply = response.choices[0].message.content.strip()
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"❌ Ошибка OpenAI: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

# Инициализация бота
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Бот запущен.")
app.run_polling()
