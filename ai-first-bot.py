import os
import signal
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import aiohttp

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
                print("OpenRouter API response:", result)  # Лог в консоль

                # Проверка структуры ответа
                if (
                    "choices" in result and
                    len(result["choices"]) > 0 and
                    "message" in result["choices"][0] and
                    "content" in result["choices"][0]["message"]
                ):
                    reply = result["choices"][0]["message"]["content"]
                    await update.message.reply_text(reply)
                else:
                    # Если структура неожиданная — сообщаем в чат
                    err_msg = (
                        "Не удалось получить ответ от AI. "
                        "Пожалуйста, свяжитесь с @ar248fi."
                    )
                    await update.message.reply_text(err_msg)
                    print("Ошибка: некорректный ответ API:", result)

    except Exception as e:
        err_text = f"Ошибка при обращении к AI: {e}. Пожалуйста, свяжитесь с @ar248fi."
        await update.message.reply_text(err_text)
        print("Ошибка при обращении к OpenRouter:", e)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.initialize()
    await app.start()

    print("Бот запущен и слушает сообщения...")

    stop_event = asyncio.Event()

    def shutdown():
        print("Получен сигнал остановки, завершаем работу...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    await stop_event.wait()

    await app.stop()
    await app.shutdown()
    print("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
