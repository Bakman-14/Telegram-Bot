import asyncio
import logging
import os
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import web  # Імпортуємо web для запуску сервера-заглушки

# Імпортуємо конфіг з config.py
from config import BOT_TOKEN, setup_logging
# Імпортуємо функції БД з database.py
from database import init_db
# Імпортуємо фоновий цикл з reminder_loop.py
from reminder_loop import reminder_loop
# Імпортуємо обробники з handlers.py
from handlers import setup_handlers

# Налаштовуємо логування за допомогою функції з config.py
setup_logging()

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Реєструємо всі обробники команд та FSM
setup_handlers(dp)


# ============================================================================
# ВЕБСЕРВЕР ДЛЯ RENDER (HEALTH CHECK)
# ============================================================================
async def handle_health_check(request: web.Request) -> web.Response:
    """Простий обробник запитів, який повертає статус 'OK'."""
    return web.Response(text="Bot is running!", status=200)


async def start_web_server() -> web.TCPSite:
    """Запускає вебсервер на порту, який надає хостинг (за замовчуванням 10000)."""
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render динамічно передає порт через змінну оточення PORT
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info("Вебсервер запущено на порту %s", port)
    return site


# ============================================================================
# ГОЛОВНА ФУНКЦІЯ
# ============================================================================
async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set. Скопіюй .env.example у .env і додай свій токен."
        )
    
    proxy_url = os.getenv("TELEGRAM_PROXY")

    if proxy_url:
        session = AiohttpSession(proxy=proxy_url)
        bot = Bot(token=BOT_TOKEN, session=session)
        logging.info("Бот запущений через проксі: %s", proxy_url)
    else:
        bot = Bot(token=BOT_TOKEN)

    await init_db()
    
    # 1. Запуск вебсервера для Render
    web_server_site = await start_web_server()
    
    # 2. Запуск фонового циклу нагадувань
    scheduler_task = asyncio.create_task(reminder_loop(bot))
    
    try:
        # 3. Запуск лонг-полінгу бота
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logging.info("Polling was cancelled")
    except Exception as exc:
        logging.exception("Polling error: %s", exc)
    finally:
        # Коректне завершення роботи
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logging.info("Scheduler task cancelled")

        # Зупиняємо вебсервер
        await web_server_site.stop()
        logging.info("Вебсервер зупинено")

        if bot:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
