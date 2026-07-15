"""
Обробники повідомлень та команд для телеграм-бота.

Цей модуль містить всі обробники @dp.message та @dp.callback_query
для команд (/start, /help, тощо) та FSM станів для створення нагадування.
"""

from datetime import datetime, timezone

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)

from database import (
    add_reminder, 
    get_user_reminders, 
    delete_reminder, 
    get_user_language,
    set_user_language 
)
from strings import get_text
from config import BOT_TOKEN, setup_logging, DEBUG_MODE
from states import ReminderStates
from utils import parse_due_datetime, format_local_datetime


# ============================================================================
# КЛАВІАТУРИ (КНОПКИ)
# ============================================================================

def get_main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, "btn_new"))],
            [KeyboardButton(text=get_text(lang, "btn_list")), KeyboardButton(text=get_text(lang, "btn_settings"))]
        ],
        resize_keyboard=True
    )

def get_cancel_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text(lang, "btn_cancel"))]],
        resize_keyboard=True
    )


def setup_handlers(dp: Dispatcher) -> None:
    
    # ------------------------------------------------------------------------
    # СКАСУВАННЯ
    # ------------------------------------------------------------------------
    @dp.message(lambda message: message.text in ["/cancel", "❌ Скасувати операцію", "❌ Cancel Operation"])
    async def global_cancel(message: Message, state: FSMContext) -> None:
        lang = await get_user_language(message.from_user.id)
        current_state = await state.get_state()
        if current_state is None:
            await message.answer(get_text(lang, "no_active_actions"), reply_markup=get_main_menu(lang))
            return
        await state.clear()
        await message.answer(get_text(lang, "cancel_ok"), reply_markup=get_main_menu(lang))

    # ------------------------------------------------------------------------
    # ГОЛОВНІ КОМАНДИ
    # ------------------------------------------------------------------------
    @dp.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇦 Українська", callback_data="set_lang_uk"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")
            ]
        ])
        await message.answer(
            "Привіт! Я бот для нагадувань. Вибери мову для продовження:\n\n"
            "Hello! I am a reminder bot. Choose a language to continue:",
            reply_markup=kb
        )
        
    @dp.callback_query(lambda c: c.data and c.data.startswith('set_lang_'))
    async def handle_set_language(callback: CallbackQuery) -> None:
        await callback.answer()
        lang = callback.data.split('_')[2]
        
        await set_user_language(callback.from_user.id, lang)
        
        await callback.message.answer(
            get_text(lang, "lang_changed") + "\n" + get_text(lang, "main_menu_intro"),
            reply_markup=get_main_menu(lang)
        )
        
    @dp.message(lambda message: message.text in ["⚙️ Налаштування", "⚙️ Settings"])
    async def cmd_settings(message: Message) -> None:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇦 Українська", callback_data="set_lang_uk"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")
            ]
        ])
        lang = await get_user_language(message.from_user.id)
        await message.answer(get_text(lang, "change_lang"), reply_markup=kb)

    @dp.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        lang = await get_user_language(message.from_user.id)
        await message.answer(get_text(lang, "help_text"), reply_markup=get_main_menu(lang))

    # ------------------------------------------------------------------------
    # FSM: СТВОРЕННЯ НАГАДУВАННЯ
    # ------------------------------------------------------------------------
    @dp.message(lambda message: message.text in ["➕ Нове нагадування", "➕ New Reminder"])
    @dp.message(Command("new"))
    async def cmd_new(message: Message, state: FSMContext) -> None:
        lang = await get_user_language(message.from_user.id)
        await state.set_state(ReminderStates.text)
        await message.answer(get_text(lang, "enter_text"), reply_markup=get_cancel_menu(lang))

    @dp.message(ReminderStates.text)
    async def process_reminder_text(message: Message, state: FSMContext) -> None:
        lang = await get_user_language(message.from_user.id)
        await state.update_data(reminder_text=message.text)
        await state.set_state(ReminderStates.due)
        await message.answer(get_text(lang, "enter_due"), reply_markup=get_cancel_menu(lang))

    @dp.message(ReminderStates.due)
    async def process_reminder_due(message: Message, state: FSMContext) -> None:
        lang = await get_user_language(message.from_user.id)
        data = await state.get_data()
        
        if not data.get("reminder_text"):
            await message.answer(get_text(lang, "something_went_wrong"), reply_markup=get_main_menu(lang))
            await state.clear()
            return

        due_dt = parse_due_datetime(message.text)
        if due_dt is None:
            await message.answer(get_text(lang, "error_date"), reply_markup=get_cancel_menu(lang))
            return

        if due_dt <= datetime.now(timezone.utc):
            await message.answer(get_text(lang, "error_past"), reply_markup=get_cancel_menu(lang))
            return

        await state.update_data(reminder_due=due_dt.isoformat())
        await state.set_state(ReminderStates.recurrence)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text(lang, "btn_yes_repeat"), callback_data="recurrence_yes"),
                InlineKeyboardButton(text=get_text(lang, "btn_no_repeat"), callback_data="recurrence_no")
            ]
        ])
        await message.answer(get_text(lang, "ask_recurrence"), reply_markup=kb)

    # ------------------------------------------------------------------------
    # CALLBACKS ДЛЯ ПОВТОРЕННЯ
    # ------------------------------------------------------------------------
    @dp.callback_query(lambda c: c.data and c.data.startswith('recurrence_'))
    async def handle_recurrence_choice(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        lang = await get_user_language(callback.from_user.id)
        data = await state.get_data()
        
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        if callback.data == "recurrence_no":
            reminder_text = data.get("reminder_text")
            due_iso = data.get("reminder_due")
            due_dt = datetime.fromisoformat(due_iso)
            
            reminder_id = await add_reminder(
                user_id=callback.from_user.id,
                chat_id=callback.message.chat.id,
                text=reminder_text,
                due_dt=due_dt,
                recurrence='none',
            )
            await state.clear()
            local_time = format_local_datetime(due_dt.isoformat())
            await callback.message.answer(
                get_text(lang, "rem_saved_single", id=reminder_id, time=local_time),
                reply_markup=get_main_menu(lang)
            )
            
        elif callback.data == "recurrence_yes":
            await state.set_state(ReminderStates.interval)
            await callback.message.answer(
                get_text(lang, "ask_interval_days"),
                reply_markup=get_cancel_menu(lang)
            )

    @dp.message(ReminderStates.interval)
    async def process_recurrence_interval(message: Message, state: FSMContext) -> None:
        lang = await get_user_language(message.from_user.id)
        txt = message.text.strip()
        
        if not txt.isdigit() or int(txt) <= 0:
            unit = get_text(lang, "unit_mins_full") if DEBUG_MODE else get_text(lang, "unit_days_full")
            await message.answer(get_text(lang, "error_num", unit=unit), reply_markup=get_cancel_menu(lang))
            return
        
        await state.update_data(recurrence_interval=int(txt))
        await state.set_state(ReminderStates.recurrence_end)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_infinite"), callback_data="rec_end_none")],
            [InlineKeyboardButton(text=get_text(lang, "btn_end_date"), callback_data="rec_end_input")]
        ])
        
        hint = "YYYY-MM-DD HH:MM" if DEBUG_MODE else "YYYY-MM-DD"
        await message.answer(get_text(lang, "choose_end_mode", hint=hint), reply_markup=kb)

    @dp.callback_query(lambda c: c.data and c.data.startswith('rec_end_'))
    async def handle_rec_end(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        lang = await get_user_language(callback.from_user.id)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        
        if callback.data == 'rec_end_none':
            data = await state.get_data()
            due_dt = datetime.fromisoformat(data.get('reminder_due'))
            interval = data.get('recurrence_interval', 1)
            
            reminder_id = await add_reminder(
                user_id=callback.from_user.id,
                chat_id=callback.message.chat.id,
                text=data.get('reminder_text'),
                due_dt=due_dt,
                recurrence='daily',
                interval=interval,
                recurrence_end=None,
            )
            await state.clear()
            local_time = format_local_datetime(due_dt.isoformat())
            unit = get_text(lang, "unit_mins") if DEBUG_MODE else get_text(lang, "unit_days")
            
            await callback.message.answer(
                get_text(lang, "rem_saved_rec", id=reminder_id, time=local_time, interval=interval, unit=unit),
                reply_markup=get_main_menu(lang)
            )
        
        elif callback.data == 'rec_end_input':
            await callback.message.answer(get_text(lang, "enter_end_date"), reply_markup=get_cancel_menu(lang))
            await state.set_state(ReminderStates.recurrence_end)

    @dp.message(ReminderStates.recurrence_end)
    async def process_recurrence_end(message: Message, state: FSMContext) -> None:
        lang = await get_user_language(message.from_user.id)
        data = await state.get_data()
        text = message.text.strip()
        
        try:
            end_date = datetime.strptime(text, "%Y-%m-%d").date()
            recurrence_end_iso = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc).isoformat()
        except ValueError:
            await message.answer(get_text(lang, "error_format"), reply_markup=get_cancel_menu(lang))
            return

        due_dt = datetime.fromisoformat(data.get("reminder_due"))
        interval = data.get("recurrence_interval", 1)
        
        reminder_id = await add_reminder(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            text=data.get("reminder_text"),
            due_dt=due_dt,
            recurrence='daily',
            interval=interval,
            recurrence_end=recurrence_end_iso,
        )
        await state.clear()
        
        await message.answer(
            get_text(lang, "rem_saved_end_date", id=reminder_id, end_date=recurrence_end_iso),
            reply_markup=get_main_menu(lang)
        )

    # ------------------------------------------------------------------------
    # СПИСОК ТА ВИДАЛЕННЯ НАГАДУВАНЬ
    # ------------------------------------------------------------------------
    @dp.message(lambda message: message.text in ["📅 Мої нагадування", "📅 My Reminders"])
    @dp.message(Command("list"))
    async def cmd_list(message: Message) -> None:
        lang = await get_user_language(message.from_user.id)
        reminders = await get_user_reminders(message.from_user.id)
        
        if not reminders:
            await message.answer(get_text(lang, "no_reminders"), reply_markup=get_main_menu(lang))
            return

        await message.answer(get_text(lang, "loading_reminders"), reply_markup=get_main_menu(lang))
        
        for row in reminders:
            # 1. Форматує дату локально
            local_time = format_local_datetime(row['due_datetime'])
            
            # 2. Отримує локалізований шаблон картки та наповнює його динамічними даними
            text_box = get_text(
                lang, 
                "reminder_display", 
                text=row['text'], 
                time=local_time
            )
            
            # 3. Якщо це повторюване нагадування, додає інформацію про інтервал
            if row.get('recurrence') == 'daily':
                interval = row.get('interval') or 1
                text_box += get_text(lang, "recurrence_info", interval=interval)
            
            # 4. Створює інлайн-кнопку видалення
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_text(lang, "btn_delete"), callback_data=f"del_{row['id']}")]
            ])
            await message.answer(text_box, reply_markup=kb, parse_mode="Markdown")

    @dp.callback_query(lambda c: c.data and c.data.startswith('del_'))
    async def handle_delete_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        lang = await get_user_language(callback.from_user.id)
        reminder_id = int(callback.data.split('_')[1])
        
        deleted = await delete_reminder(callback.from_user.id, reminder_id)
        if deleted:
            await callback.message.delete()
            await callback.message.answer(get_text(lang, "deleted_ok", id=reminder_id), reply_markup=get_main_menu(lang))
        else:
            await callback.message.answer(get_text(lang, "delete_error"), reply_markup=get_main_menu(lang))