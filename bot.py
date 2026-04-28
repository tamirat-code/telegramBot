import os
import random
import logging
import sqlite3
from datetime import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from zoneinfo import ZoneInfo
# =========================
# CONFIG
# =========================
import logging
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")  
DB_NAME = "users.db"

MESSAGES = [
    "Good morning! ☀️",
    "Rise and shine! 🌅",
    "Have a beautiful day 🌸",
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()


def add_user(chat_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()


def get_users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

# =========================
# HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)

    await update.message.reply_text(
        "👋 Welcome! You will receive daily morning messages ☀️"
    )


async def save_user_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    logging.info(f"User saved: {chat_id}")

# =========================
# JOB
# =========================

async def send_good_morning(context: ContextTypes.DEFAULT_TYPE):
    users = get_users()

    if not users:
        logging.info("No users to send messages to.")
        return

    message = random.choice(MESSAGES)

    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logging.error(f"Failed to send to {chat_id}: {e}")

# =========================
# MAIN
# =========================

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set!")

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, save_user_messages))

    # schedule (UTC time!)
    job_queue = app.job_queue
    job_queue.run_daily(
    send_good_morning,
    time=time(hour=1, minute=0, tzinfo=ZoneInfo("Africa/Addis_Ababa"))
)

    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("BOT CRASH ERROR:", e)
        raise