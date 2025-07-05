import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI
from aiolimiter import AsyncLimiter

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токенов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверка токенов
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    logger.error("TELEGRAM_TOKEN или OPENAI_API_KEY не заданы")
    raise ValueError("TELEGRAM_TOKEN или OPENAI_API_KEY не заданы")

# Асинхронный клиент OpenAI
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Ограничение запросов: 10 в минуту
limiter = AsyncLimiter(10, 60)

# Кэш ответов
response_cache = {}

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ChatGPT-бот 🤖. Напиши мне что-нибудь.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if user_message in response_cache:
        await update.message.reply_text(response_cache[user_message])
        return
    async with limiter:
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_message}]
            )
            reply = response.choices[0].message.content.strip()
            response_cache[user_message] = reply  # Сохраняем в кэш
            await update.message.reply_text(reply)
        except Exception as e:
            logger.error(f"Ошибка OpenAI: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

async def main():
    try:
        # Инициализация приложения
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Бот запущен")
        
        # Инициализация и запуск приложения
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            poll_interval=0.0,
            timeout=10,
            drop_pending_updates=True
        )
        
        # Бесконечный цикл для поддержания работы приложения
        while True:
            await asyncio.sleep(3600)  # Спать 1 час
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
