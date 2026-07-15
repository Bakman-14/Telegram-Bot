"""
Фоновий цикл для надсилання нагадувань.

Цей модуль містить основну логіку для періодичної перевірки та надсилання
нагадувань користувачам через Telegram бота.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta  # Додали timedelta

# Імпортуємо REMINDER_CHECK_INTERVAL та додаємо DEBUG_MODE
from config import REMINDER_CHECK_INTERVAL, DEBUG_MODE
from database import (
    fetch_due_reminders,
    mark_reminder_sent,
    update_reminder_due,
)
from utils import compute_next_due_daily


async def reminder_loop(bot) -> None:
    """Фоновий цикл, який надсилає нагадування, коли настає час.
    
    Алгоритм:
    1. Кожні REMINDER_CHECK_INTERVAL секунд (за замовчуванням 30)
    2. Отримуємо всі нагадування, час яких вже настав (due_datetime <= now)
    3. Для кожного нагадування:
       - Надсилаємо повідомлення в Telegram чат
       - Якщо це одноразове — позначуємо як надіслане (sent=1, active=0)
       - Якщо це щодневне — обчислюємо наступний час та оновлюємо БД
       - Якщо є дата закінчення — відключаємо нагадування після цієї дати
    4. При скасуванні (Ctrl+C) коректно завершуємо роботу
    
    Аргументи:
        bot: Об'єкт Bot від aiogram для надсилання повідомлень
        
    Приклади помилок, які обробляються:
        - Невдала відправка повідомлення (мережа) — логуємо помилку і продовжуємо
        - Малформовані дати у БД — позначуємо нагадування як надіслане
        - asyncio.CancelledError — граціозне завершення з логуванням
    """
    try:
        while True:
            try:
                reminders = await fetch_due_reminders()
                now = datetime.now(timezone.utc)
                
                for reminder in reminders:
                    text = f"⏰ Нагадування #{reminder['id']}: {reminder['text']}"
                    
                    # Спроба надіслати повідомлення
                    try:
                        await bot.send_message(reminder["chat_id"], text)
                        logging.info("Sent reminder %s", reminder["id"])
                    except Exception as exc:
                        logging.error(
                            "Не вдалося надіслати нагадування %s: %s",
                            reminder["id"],
                            exc,
                        )
                        # Не модифікуємо нагадування — спробуємо ще раз пізніше
                        continue

                    # Обробка після надсилання: одноразове або повторюване
                    rec = reminder.get('recurrence') or 'none'
                    
                    if rec == 'none' or not rec:
                        # Одноразове нагадування — позначуємо як надіслане
                        await mark_reminder_sent(reminder['id'])
                    
                    elif rec == 'daily':
                        # Щодневне нагадування — обчислюємо наступний час
                        try:
                            due_dt = datetime.fromisoformat(reminder['due_datetime'])
                        except Exception:
                            # Малформована дата — позначуємо як надіслане, щоб не зацикліти
                            await mark_reminder_sent(reminder['id'])
                            continue
                        
                        interval = int(reminder.get('interval') or 1)
                        # ====================================================
                        # ДЕБАГ-РЕЖИМ
                        # ====================================================
                        if DEBUG_MODE:
                            # У дебаг-режимі додаємо ХВИЛИНИ від поточного часу
                            next_due = now + timedelta(minutes=interval)
                        else:
                            # У звичайному режимі використовуємо стандартну функцію (дні)
                            next_due = compute_next_due_daily(due_dt, now, interval)
                        # ====================================================
                        rec_end = reminder.get('recurrence_end')
                        
                        if rec_end:
                            # Є дата закінчення — перевіряємо, чи не перейшли за неї
                            try:
                                end_dt = datetime.fromisoformat(rec_end)
                            except Exception:
                                end_dt = None
                            
                            if end_dt and next_due > end_dt:
                                # Наступний час вже після дати закінчення — зупиняємо
                                await mark_reminder_sent(reminder['id'])
                            else:
                                # Ще в межах — оновлюємо час
                                await update_reminder_due(reminder['id'], next_due.isoformat())
                        else:
                            # Немає дати закінчення — оновлюємо час
                            await update_reminder_due(reminder['id'], next_due.isoformat())
                    
                    else:
                        # Невідомий тип повторення — позначуємо як надіслане для безпеки
                        await mark_reminder_sent(reminder['id'])
                        
            except Exception as exc:
                logging.exception("Помилка фонового циклу нагадувань: %s", exc)

            # Чекаємо перед наступною перевіркою
            await asyncio.sleep(REMINDER_CHECK_INTERVAL)
            
    except asyncio.CancelledError:
        logging.info("reminder_loop was cancelled, exiting gracefully")
        raise
