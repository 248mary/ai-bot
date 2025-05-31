import os
import signal
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import aiohttp

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения!")
if OPENROUTER_API_KEY is None:
    raise ValueError("OPENROUTER_API_KEY не найден в переменных окружения!")

# Глобальная aiohttp сессия (одна на весь бот)
session: aiohttp.ClientSession | None = None

# Для хранения имени пользователя в памяти (по user_id)
user_names = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name or 'друг'}! Я АИ-бот от @ar248fi — с радостью отвечу на любой интересующий тебя вопрос.\n"
        "Как я могу к тебе обращаться?"
    )
    # Удаляем старое имя (если было)
    user_names.pop(user.id, None)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global session
    user = update.effective_user
    text = update.message.text.strip()

    # Если имя ещё не сохранено — считаем это именем
    if user.id not in user_names:
        user_names[user.id] = text
        await update.message.reply_text(f"Отлично, {text}! Теперь можешь задавать мне любые вопросы.")
        return

    # Формируем запрос к OpenRouter API
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Ты дружелюбный AI-ассистент."},
            {"role": "user", "content": text}
        ],
    }

    try:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        ) as resp:
            result = await resp.json()

            # Проверяем структуру ответа
            if (
                "choices" in result and
                len(result["choices"]) > 0 and
                "message" in result["choices"][0] and
                "content" in result["choices"][0]["message"]
            ):
                reply = result["choices"][0]["message"]["content"]
                await update.message.reply_text(reply)
            else:
                await update.message.reply_text(
                    "Извините, не смог получить ответ от AI. Пожалуйста, свяжитесь с @ar248fi."
                )
    except Exception as e:
        await update.message.reply_text(
            f"Произошла ошибка при обращении к AI: {e}\nПожалуйста, свяжитесь с @ar248fi."
        )

async def on_startup(app):
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()

async def on_shutdown(app):
    global session
    if session and not session.closed:
        await session.close()

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    print("Бот запущен и слушает сообщения...")

    # Запуск бота
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (RuntimeError, KeyboardInterrupt):
        # Обработка перезапуска и Ctrl+C
        pass
