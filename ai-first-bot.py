import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import aiohttp
import asyncio

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения!")
if OPENROUTER_API_KEY is None:
    raise ValueError("OPENROUTER_API_KEY не найден в переменных окружения!")

async def start(update, context):
    user = update.effective_user
    name = user.first_name or "друг"
    await update.message.reply_text(
        f"Привет, {name}! Я АИ-бот от @ar248fi — с радостью отвечу на любой интересующий тебя вопрос.\n"
        f"Как я могу к тебе обращаться?"
    )

async def handle_message(update, context):
    user_message = update.message.text
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_message}]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                result = await response.json()
                reply = result["choices"][0]["message"]["content"]
                await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Произошла ошибка при обращении к AI. Попробуй позже.")
        print("Ошибка при обращении к OpenRouter:", e)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.initialize()
    await app.start()

    print("Бот запущен и слушает сообщения...")

    # Ждём, пока приложение не будет остановлено (например, Ctrl+C)
    await app.wait_closed()

    await app.stop()
    await app.shutdown()
    print("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
