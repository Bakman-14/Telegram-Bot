# ============================================================================
# СЛОВНИК ЛОКАЛІЗАЦІЇ
# ============================================================================

# ============================================================================
# СЛОВНИК ЛОКАЛІЗАЦІЇ
# ============================================================================

MESSAGES = {
    "uk": {
        "welcome": "Привіт! Я бот для нагадувань. Вибери мову для продовження / Choose a language to continue:",
        "main_menu_intro": "Використовуй кнопки нижче для навігації.",
        "btn_new": "➕ Нове нагадування",
        "btn_list": "📅 Мої нагадування",
        "btn_settings": "⚙️ Налаштування",
        "btn_cancel": "❌ Скасувати операцію",
        "cancel_ok": "Операцію скасовано.",
        "no_active_actions": "Зараз немає активних операцій.",
        "help_text": (
            "Я допоможу не забути про важливі справи.\n\n"
            "• Натискай **➕ Нове нагадування**, щоб створити запис.\n"
            "• Натискай **📅 Мої нагадування**, щоб переглянути або видалити існуючі.\n"
            "• Формат часу при створенні: `YYYY-MM-DD HH:MM` (наприклад, 2026-07-15 14:00)"
        ),
        "enter_text": "Напиши текст нагадування:",
        "enter_due": "Введи дату і час для нагадування у форматі YYYY-MM-DD HH:MM.\nНаприклад: 2026-07-15 14:00",
        "error_date": "Не зміг розпізнати дату. Спробуй ще раз (наприклад: 2026-07-15 14:00):",
        "error_past": "Час вже минув. Введи майбутню дату та час:",
        "reminder_display": "🔔 **{text}**\n🕒 Час: {time}",
        "something_went_wrong": "Щось пішло не так. Почни знову командою /new.",
        "ask_recurrence": "Повторювати це нагадування періодично?",
        "btn_yes_repeat": "✅ Так, повторювати",
        "btn_no_repeat": "❌ Ні, один раз",
        "btn_infinite": "♾️ Без кінця",
        "recurrence_info": "\n🔄 Повтор: кожні {interval} дн.",
        "btn_end_date": "📅 Ввести дату закінчення",
        "ask_interval_days": "Через скільки днів повторювати? Введи число (1 — кожного дня):",
        "error_num": "Введи додатнє ціле число {unit} (наприклад 1):",
        "choose_end_mode": "Вибери режим закінчення повторень (якщо дата, то формат {hint}):",
        "enter_end_date": "Введи кінцеву дату у форматі YYYY-MM-DD:",
        "rem_saved_single": "Готово! Одноразове нагадування #{id} збережено.\nЯ нагадаю {time}.",
        "rem_saved_rec": "Готово! Нагадування #{id} збережено.\nВперше: {time}, далі — кожні {interval} {unit}.",
        "rem_saved_end_date": "Готово! Нагадування #{id} успішно створено до {end_date}.",
        "no_reminders": "У тебе немає запланованих нагадувань.",
        "loading_reminders": "Завантажую твої нагадування...",
        "btn_delete": "🗑️ Видалити",
        "deleted_ok": "✅ Нагадування #{id} видалено.",
        "delete_error": "Не вдалося видалити нагадування (можливо, воно вже застаріло).",
        "change_lang": "Вибери мову / Choose a language:",
        "lang_changed": "Мову змінено на українську! 🇺🇦",
        "error_format": "Неправильний формат. Введи дату як YYYY-MM-DD:",
        "unit_days_full": "днів",
        "unit_mins_full": "хвилин",
        "unit_days": "дн",
        "unit_mins": "хв",
    },
    "en": {
        "welcome": "Hello! I am a reminder bot. Choose a language to continue / Вибери мову для продовження:",
        "main_menu_intro": "Use the buttons below to navigate.",
        "btn_new": "➕ New Reminder",
        "btn_list": "📅 My Reminders",
        "btn_settings": "⚙️ Settings",
        "btn_cancel": "❌ Cancel Operation",
        "cancel_ok": "Operation cancelled.",
        "no_active_actions": "There are no active operations.",
        "help_text": (
            "I will help you not to forget about important things.\n\n"
            "• Press **➕ New Reminder** to create an entry.\n"
            "• Press **📅 My Reminders** to view or delete existing ones.\n"
            "• Time format during creation: `YYYY-MM-DD HH:MM` (e.g., 2026-07-15 14:00)"
        ),
        "enter_text": "Write the reminder text:",
        "enter_due": "Enter the date and time for the reminder in YYYY-MM-DD HH:MM format.\nExample: 2026-07-15 14:00",
        "error_date": "Could not recognize the date. Try again (e.g., 2026-07-15 14:00):",
        "error_past": "This time has already passed. Please enter a future date and time:",
        "reminder_display": "🔔 **{text}**\n🕒 Time: {time}",
        "something_went_wrong": "Something went wrong. Start over with /new.",
        "ask_recurrence": "Repeat this reminder periodically?",
        "btn_yes_repeat": "✅ Yes, repeat",
        "btn_no_repeat": "❌ No, once",
        "btn_infinite": "♾️ Infinite",
        "recurrence_info": "\n🔄 Recurrence: every {interval} days.",
        "btn_end_date": "📅 Enter End Date",
        "ask_interval_days": "How many days to repeat? Enter a number (1 — every day):",
        "error_num": "Enter a positive integer {unit} (e.g. 1):",
        "choose_end_mode": "Select the end mode of repetitions (if date, then format {hint}):",
        "enter_end_date": "Enter the end date in YYYY-MM-DD format:",
        "rem_saved_single": "Done! One-time reminder #{id} saved.\nI will remind you at {time}.",
        "rem_saved_rec": "Done! Reminder #{id} saved.\nFirst run: {time}, then — every {interval} {unit}.",
        "rem_saved_end_date": "Done! Reminder #{id} successfully created until {end_date}.",
        "no_reminders": "You have no scheduled reminders.",
        "loading_reminders": "Loading your reminders...",
        "btn_delete": "🗑️ Delete",
        "deleted_ok": "✅ Reminder #{id} deleted.",
        "delete_error": "Failed to delete reminder.",
        "change_lang": "Choose a language / Вибери мову:",
        "lang_changed": "Language changed to English! 🇬🇧",
        "error_format": "Invalid format. Enter date as YYYY-MM-DD:",
        "unit_days_full": "days",
        "unit_mins_full": "minutes",
        "unit_days": "days",
        "unit_mins": "min",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    """Зручна хелпер-функція для отримання тексту за ключем."""
    text = MESSAGES.get(lang, MESSAGES["uk"]).get(key, f"[{key}]")
    if kwargs:
        return text.format(**kwargs)
    return text