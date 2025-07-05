import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI  # Используем OpenAI SDK для Together

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токенов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")  # Используем новое имя переменной

# Проверка токенов
if not TELEGRAM_TOKEN or not TOGETHER_API_KEY:
    logger.error("TELEGRAM_TOKEN или TOGETHER_API_KEY не заданы")
    raise ValueError("TELEGRAM_TOKEN или TOGETHER_API_KEY не заданы")

# Клиент Together.ai
client = AsyncOpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.xyz/v1"  # ОБЯЗАТЕЛЬНО для Together.ai
)

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Меня зовут XGPT 👾. Напиши мне что-нибудь.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        response = await client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {
                    "role": "system",
                    "content": "Ты — умный, дружелюбный помощник. Всегда отвечай исключительно на русском языке, даже если вопрос задан на английском."
                },
                {
                    "role": "user",
                    "content": f"Ответь на русском языке на следующее: {user_message}"
                }
            ]
        )
        reply = response.choices[0].message.content.strip()
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Ошибка Together.ai: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
async def main():
    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Бот запущен")

        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            poll_interval=0.0,
            timeout=10,
            drop_pending_updates=True
        )

        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
