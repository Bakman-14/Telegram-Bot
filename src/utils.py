"""
Утиліти та допоміжні функції для телеграм-бота.

Цей модуль містить функції для роботи з часом, парсингу вводу користувача
та обчислень для рекурентних нагадувань.
"""

from datetime import datetime, timezone, timedelta


def local_timezone() -> timezone:
    """Повертає часовий пояс системи, щоб показувати локальний час користувачу.
    
    Returns:
        timezone: Об'єкт часового поясу, який відповідає локальній машині
        
    Example:
        >>> tz = local_timezone()
        >>> dt = datetime.now(tz)
    """
    return datetime.now().astimezone().tzinfo


def format_local_datetime(utc_iso: str) -> str:
    """Форматує UTC час (ISO формат) на локальний час для показу користувачу.
    
    Args:
        utc_iso: ISO-формат рядок дати/часу у UTC (напр. '2026-07-15T10:30:00+00:00')
        
    Returns:
        str: Локальний час у форматі YYYY-MM-DD HH:MM
        
    Example:
        >>> utc_iso = "2026-07-15T10:30:00+00:00"
        >>> local_str = format_local_datetime(utc_iso)
        >>> print(local_str)  # наприклад: 2026-07-15 13:30
    """
    utc_dt = datetime.fromisoformat(utc_iso)
    local_dt = utc_dt.astimezone(local_timezone())
    return local_dt.strftime("%Y-%m-%d %H:%M")


def parse_due_datetime(text: str) -> datetime | None:
    """Розбирає дату/час у форматі YYYY-MM-DD HH:MM або YYYY-MM-DDTHH:MM.

    Зберігає час у UTC всередині бота. Якщо користувач не вказав таймзону,
    ми вважаємо, що це локальний час машини.
    
    Args:
        text: Рядок від користувача (напр. '2026-07-15 10:30' або '2026-07-15T10:30')
        
    Returns:
        datetime | None: Datetime об'єкт у UTC, або None якщо не вдалося розібрати
        
    Example:
        >>> dt = parse_due_datetime("2026-07-15 14:30")
        >>> if dt:
        ...     print(f"Нагадування на {dt}")
        ... else:
        ...     print("Невірний формат")
    """
    text = text.strip()
    # Пробуємо два поширені формати вводу
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            # Розпізнаємо як локальний час (без таймзони)
            naive = datetime.strptime(text, fmt)
            # Привласнюємо локальну таймзону
            tz = local_timezone()
            # Конвертуємо в UTC для внутрішнього зберігання
            return naive.replace(tzinfo=tz).astimezone(timezone.utc)
        except ValueError:
            # Формат не підходить, пробуємо наступний
            continue
    return None


def compute_next_due_daily(due_dt: datetime, now: datetime, interval: int) -> datetime:
    """Обчислює наступний час для щодення повторюваного нагадування.
    
    Алгоритм:
    1. Беремо попередній час (due_dt) і додаємо інтервал (N днів)
    2. Якщо цей час уже минув (меньше за поточний час), додаємо ще N днів
    3. Повторюємо доти, поки не знайдемо час у майбутньому
    
    Це робиться, щоб уникнути "повені" повідомлень, коли бот перезавантажується
    після простоя. Замість того, щоб надіслати 10 нагадувань одразу,
    надсилаємо найближче майбутнє.
    
    Args:
        due_dt: Попередній час нагадування (timezone-aware UTC datetime)
        now: Поточний час (timezone-aware UTC datetime)
        interval: Інтервал у днях (напр. 1 для щодня, 3 для кожні 3 дні)
        
    Returns:
        datetime: Наступний час для надсилання нагадування (UTC)
        
    Example:
        >>> from datetime import datetime, timezone
        >>> due = datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc)
        >>> now = datetime(2026, 7, 20, 15, 30, 0, tzinfo=timezone.utc)
        >>> next_due = compute_next_due_daily(due, now, 1)
        >>> # next_due буде 2026-07-21 10:00 (наступний день)
    """
    if interval is None or interval <= 0:
        interval = 1
    
    delta = timedelta(days=interval)
    next_due = due_dt + delta
    
    # Додаємо інтервалів, доки не перейдемо в майбутнє
    while next_due <= now:
        next_due += delta
    
    return next_due
