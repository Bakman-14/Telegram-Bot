import asyncio
import logging
import os
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import web

# Імпортує конфіг з config.py
from config import BOT_TOKEN, setup_logging
# Імпортує функції БД з database.py
from database import init_db
# Імпортує фоновий цикл з reminder_loop.py
from reminder_loop import reminder_loop
# Імпортує обробники з handlers.py
from handlers import setup_handlers

setup_logging()

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
setup_handlers(dp)

# Глобальні змінні для контролю фонових тасків
bot_polling_task = None
scheduler_task = None

# ============================================================================
# ВЕБСЕРВЕР (HEALTH CHECK)
# ============================================================================
async def handle_health_check(request: web.Request) -> web.Response:
    """Миттєво відповідає на запити Render."""
    return web.Response(text="Bot is active and running!", status=200)


async def on_startup(app: web.Application) -> None:
    """Викликається автоматично при старті вебсервера."""
    global bot_polling_task, scheduler_task
    
    await init_db()
    
    # Створює бота
    proxy_url = os.getenv("TELEGRAM_PROXY")
    if proxy_url:
        session = AiohttpSession(proxy=proxy_url)
        bot = Bot(token=BOT_TOKEN, session=session)
    else:
        bot = Bot(token=BOT_TOKEN)
        
    app['bot'] = bot

    # Запускає лонг-полінг та цикл нагадувань як фонові таски вебсервера
    bot_polling_task = asyncio.create_task(dp.start_polling(bot))
    scheduler_task = asyncio.create_task(reminder_loop(bot))
    logging.info("Фонові таски бота та планувальника успішно запущені.")


async def on_cleanup(app: web.Application) -> None:
    """Викликається автоматично при зупинці вебсервера."""
    global bot_polling_task, scheduler_task
    logging.info("Зупинка сервісу: очищення фонових тасків...")
    
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logging.info("Scheduler task stopped.")
            
    if bot_polling_task:
        bot_polling_task.cancel()
        try:
            await bot_polling_task
        except asyncio.CancelledError:
            logging.info("Polling stopped.")

    bot = app.get('bot')
    if bot:
        await bot.session.close()
        logging.info("Сесію бота закрито.")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set.")
        
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    
    # Реєструє хуки старту та завершення програми
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    port = int(os.getenv("PORT", 10000))
    # Запускає вебсервер у блокуючому режимі. Він буде головним процесом!
    web.run_app(app, host="0.0.0.0", port=port, access_log=None)


if __name__ == "__main__":
    main()
