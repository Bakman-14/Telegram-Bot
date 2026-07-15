"""
Модуль для роботи з базою даних SQLite нагадувань.

Цей модуль містить функції для:
- Ініціалізації схеми БД
- Додавання, видалення, отримання нагадувань
- Пошуку актуальних нагадувань для надсилання
- Оновлення статусу та часу нагадувань
"""

from datetime import datetime, timezone

import aiosqlite

from config import DB_PATH


async def init_db() -> None:
    """Ініціалізує схему бази даних.
    
    Створює таблицю reminders, якщо вона не існує.
    Безпечно додає нові колони для рекурентних нагадувань,
    якщо вони вже не існують (використовується при оновленні).
    
    Схема таблиці reminders:
    - id: автоінкрементний первинний ключ
    - user_id: ID користувача Telegram
    - chat_id: ID чату, куди надсилати повідомлення
    - text: текст нагадування
    - due_datetime: час для надсилання (ISO формат UTC)
    - created_at: час створення нагадування
    - sent: флаг, чи вже надіслано (1/0)
    - recurrence: 'none' або 'daily'
    - interval: інтервал повторення в днях (за замовчуванням 1)
    - recurrence_end: дата закінчення повторень (опціонально)
    - active: чи активне нагадування (1/0)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                due_datetime TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sent INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Безпечно додаємо колони для рекурентних нагадувань
        # (якщо вони вже існують, не буде помилки)
        cursor = await db.execute("PRAGMA table_info(reminders)")
        rows = await cursor.fetchall()
        existing_cols = [r[1] for r in rows]
        
        if 'recurrence' not in existing_cols:
            await db.execute("ALTER TABLE reminders ADD COLUMN recurrence TEXT DEFAULT 'none'")
        if 'interval' not in existing_cols:
            await db.execute("ALTER TABLE reminders ADD COLUMN interval INTEGER DEFAULT 1")
        if 'recurrence_end' not in existing_cols:
            await db.execute("ALTER TABLE reminders ADD COLUMN recurrence_end TEXT DEFAULT NULL")
        if 'active' not in existing_cols:
            await db.execute("ALTER TABLE reminders ADD COLUMN active INTEGER DEFAULT 1")
        
        await db.commit()
        
    #  Створення таблиці користувачів (якщо її немає)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'uk'
            )
        """)
        await db.commit()


async def add_reminder(
    user_id: int,
    chat_id: int,
    text: str,
    due_dt: datetime,
    *,
    recurrence: str = 'none',
    interval: int = 1,
    recurrence_end: str | None = None,
) -> int:
    """Додає нове нагадування до бази даних.
    
    Args:
        user_id: ID користувача Telegram
        chat_id: ID чату для надсилання
        text: текст нагадування
        due_dt: час для надсилання (datetime об'єкт)
        recurrence: 'none' або 'daily' (за замовчуванням 'none')
        interval: інтервал повторення в днях (за замовчуванням 1)
        recurrence_end: дата закінчення повторень (ISO рядок або None)
        
    Returns:
        int: ID новоствореного нагадування
        
    Example:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2026, 7, 15, 14, 30, tzinfo=timezone.utc)
        >>> reminder_id = await add_reminder(123456, 123456, "Купити молоко", dt)
        >>> print(f"Додано нагадування #{reminder_id}")
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO reminders
            (user_id, chat_id, text, due_datetime, created_at, recurrence, interval, recurrence_end, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                user_id,
                chat_id,
                text,
                due_dt.isoformat(),
                datetime.now(timezone.utc).isoformat(),
                recurrence,
                interval,
                recurrence_end,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_reminders(user_id: int) -> list[dict]:
    """Отримує всі активні нагадування користувача.
    
    Args:
        user_id: ID користувача Telegram
        
    Returns:
        list[dict]: Список нагадувань, відсортований за часом
        
    Example:
        >>> reminders = await get_user_reminders(123456)
        >>> for r in reminders:
        ...     print(f"#{r['id']}: {r['text']}")
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, text, due_datetime, recurrence, interval, recurrence_end
            FROM reminders
            WHERE user_id = ? AND active = 1
            ORDER BY due_datetime
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_reminder(user_id: int, reminder_id: int) -> bool:
    """Видаляє нагадування, якщо воно не було надіслано.
    
    Args:
        user_id: ID користувача (перевірка дозволу)
        reminder_id: ID нагадування для видалення
        
    Returns:
        bool: True якщо видалено, False якщо не знайдено
        
    Example:
        >>> deleted = await delete_reminder(123456, 5)
        >>> if deleted:
        ...     print("Нагадування видалено")
        ... else:
        ...     print("Не знайдено")
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM reminders WHERE id = ? AND user_id = ? AND sent = 0",
            (reminder_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def fetch_due_reminders() -> list[dict]:
    """Отримує всі нагадування, які потребують надсилання зараз.
    
    Пошукує нагадування, де due_datetime <= поточний час
    і статус активний.
    
    Returns:
        list[dict]: Список нагадувань для надсилання
        
    Example:
        >>> due_reminders = await fetch_due_reminders()
        >>> for reminder in due_reminders:
        ...     await bot.send_message(reminder['chat_id'], reminder['text'])
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, chat_id, text, due_datetime, recurrence, interval, recurrence_end
            FROM reminders
            WHERE active = 1 AND due_datetime <= ?
            ORDER BY due_datetime
            """,
            (now_utc,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def mark_reminder_sent(reminder_id: int) -> None:
    """Позначає нагадування як надіслане та деактивує його.
    
    Використовується для одноразових нагадувань.
    
    Args:
        reminder_id: ID нагадування
        
    Example:
        >>> await mark_reminder_sent(5)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE reminders SET sent = 1, active = 0 WHERE id = ?",
            (reminder_id,),
        )
        await db.commit()


async def update_reminder_due(reminder_id: int, next_due_iso: str) -> None:
    """Оновлює час наступного надсилання для рекурентного нагадування.
    
    Використовується при обробці повторюваних нагадувань.
    Нагадування залишається активним для наступного надсилання.
    
    Args:
        reminder_id: ID нагадування
        next_due_iso: новий час (ISO формат UTC)
        
    Example:
        >>> from datetime import datetime, timezone, timedelta
        >>> now = datetime.now(timezone.utc)
        >>> next_time = (now + timedelta(days=1)).isoformat()
        >>> await update_reminder_due(5, next_time)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE reminders SET due_datetime = ?, sent = 0 WHERE id = ?",
            (next_due_iso, reminder_id),
        )
        await db.commit()
        
async def get_user_language(user_id: int) -> str:
    """Повертає мову користувача (за замовчуванням 'uk')."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Спочатку намагається дізнатися мову
        async with db.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            
            # Якщо користувача немає, створює його за допомогою безпечного INSERT OR IGNORE.
            # Навіть якщо два таски спробують зробити це одночасно, помилки НЕ буде.
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)", 
                (user_id, 'uk')
            )
            await db.commit()
            
            # На випадок, якщо щойно інший таск його вже створив, 
            # або щойно його створили — повертає дефолтну мову 'uk'
            return 'uk'

async def set_user_language(user_id: int, lang: str) -> None:
    """Оновлює мову користувача."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, language) 
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
        """, (user_id, lang))
        await db.commit()
