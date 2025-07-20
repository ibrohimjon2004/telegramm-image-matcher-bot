import os
import logging
import sqlite3
from PIL import Image
import imagehash
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
)

# --- CONFIG ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
DB_PATH = "rasm_hash.db"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS hashes (id INTEGER PRIMARY KEY AUTOINCREMENT, hash TEXT)"
    )
    conn.commit()
    conn.close()

def save_hash(img_hash: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO hashes (hash) VALUES (?)", (img_hash,))
    conn.commit()
    conn.close()

def is_duplicate(img_hash: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT 1 FROM hashes WHERE hash = ?", (img_hash,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

# --- HANDLERS ---
def start(update: Update, context):
    update.message.reply_text("👋 Salom! Rasm yuboring, men mavjudligini tekshiraman.")

def handle_photo(update: Update, context):
    try:
        # Download the highest resolution photo
        photo = update.message.photo[-1]
        file = photo.get_file()
        path = file.download_to_drive()

        # Compute perceptual hash
        img = Image.open(path)
        img_hash = str(imagehash.average_hash(img))

        # Check and respond
        if is_duplicate(img_hash):
            update.message.reply_text("🟡 Bu rasm ilgari yuborilgan.")
        else:
            save_hash(img_hash)
            update.message.reply_text("🆕 Yangi rasm. Xotiraga saqlandi.")

        # Clean up
        os.remove(path)

    except Exception as e:
        logger.error(f"Xatolik rasmni qayta ishlashda: {e}")
        update.message.reply_text("❌ Rasmni tekshirishda muammo bo‘ldi.")

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Bot ishga tushmoqda...")
    app.run_polling()
