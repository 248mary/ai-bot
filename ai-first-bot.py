# Создаём сессию вне функции, чтобы переиспользовать
session = aiohttp.ClientSession()

async def handle_message(update, context):
    user_message = update.message.text
    print("Получено сообщение от пользователя:", user_message)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_message}]
    }
    try:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            result = await response.json()
            print("OpenRouter API response:", result)

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
                    "Не удалось получить ответ от AI. Пожалуйста, свяжитесь с @ar248fi."
                )
                print("Ошибка: некорректный ответ API:", result)
    except Exception as e:
        err_text = f"Ошибка при обращении к AI: {e}. Пожалуйста, свяжитесь с @ar248fi."
        await update.message.reply_text(err_text)
        print("Ошибка при обращении к OpenRouter:", e)

# Не забудь закрыть сессию при остановке приложения!
async def on_shutdown(app):
    await session.close()
