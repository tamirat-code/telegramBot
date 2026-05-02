from flask import Flask # pyright: ignore[reportMissingImports]
import threading
import os
import random
import logging
import sqlite3
from datetime import time
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# FLASK APP
# =========================
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running"

def run_flask():
    web_app.run(host="0.0.0.0", port=10000)

# =========================
# BOT CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = "users.db"

logging.basicConfig(level=logging.INFO)

MESSAGES = [
    "Good morning! ☀️",
    "Rise and shine! 🌅",
    "Have a beautiful day 🌸",
]

# =========================
# DB
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_user(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(">>> START HIT")
    logging.info(">>> START HIT")
    chat_id = update.effective_chat.id
    add_user(chat_id)
    logging.info("START COMMAND TRIGGERED")  # IMPORTANT TEST LINE

    await update.message.reply_text(
        "👋 Welcome! You will receive daily morning messages ☀️"
    )

# =========================
# JOB
# =========================
async def send_good_morning(context: ContextTypes.DEFAULT_TYPE):
    users = get_users()
    if not users:
        return

    msg = random.choice(MESSAGES)

    for chat_id in users:
        try:
            await context.bot.send_message(chat_id, msg)
        except Exception as e:
            logging.error(e)

# =========================
# BOT RUNNER
# =========================
def run_bot():
    logging.info(">>> BOT STARTING NOW")
    if not TOKEN:
        raise ValueError("BOT_TOKEN missing")

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    job_queue = app.job_queue
    job_queue.run_daily(
    send_good_morning,
    time=time(hour=7, minute=0, tzinfo=ZoneInfo("Africa/Addis_Ababa"))
      )    
    logging.info("Bot is running...")
    app.run_polling()

# =========================
# MAIN ENTRY
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()