# Telegram Reminder Bot ⏰

A simple and convenient Telegram bot for creating and managing reminders with the ability to set recurring intervals.

## 🚀 Functionality
* **Main menu** with Reply buttons for quick navigation.
* **Step-by-step creation of reminders** using FSM (Finite State Machine).
* **Repeating reminders** (every $N$ days or minutes in debug mode).
* **Reminder management** — viewing the list of upcoming events and convenient deletion using Inline buttons `🗑️ Delete`.
* **Background asynchronous loop** for regular checking and sending reminders.

## 📁 Project structure
* `src/bot.py` — entry point, launching the bot and web server.
* `src/handlers.py` — logic for processing messages, buttons, and states.
* `src/database.py` — interaction with the local SQLite database.
* `src/reminder_loop.py` — background database check loop.
* `src/config.py` — configuration variables and logging.

## ⚙️ Local launch (Windows)
1. Create a copy of the `.env` file with your unique `BOT_TOKEN`.
2. Run the `run.bat` file — it will automatically create a virtual environment (`venv`), install dependencies, and launch the bot.