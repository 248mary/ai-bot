import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai  # если используете openrouter через OpenAI-совместимый API
import aiohttp

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения!")

async def start(update, context):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"Привет, {name}! Я АИ-бот от @ar248fi — с радостью отвечу на любой вопрос.\nКак я могу к тебе обращаться?"
    )

async def handle_message(update, context):
    user_message = update.message.text
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_message}]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data) as resp:
            data = await resp.json()
            ai_response = data["choices"][0]["message"]["content"]
            await update.message.reply_text(ai_response)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
