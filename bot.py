import os
import logging
import sqlite3
from PIL import Image
import imagehash
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_PATH = "rasm_hash.db"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure DB exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS hashes (id INTEGER PRIMARY KEY AUTOINCREMENT, hash TEXT)")
    conn.commit()
    conn.close()

# Add hash to database
def save_hash(img_hash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO hashes (hash) VALUES (?)", (str(img_hash),))
    conn.commit()
    conn.close()

# Check if hash already exists
def is_duplicate(img_hash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT hash FROM hashes")
    existing_hashes = [row[0] for row in c.fetchall()]
    conn.close()
    return str(img_hash) in existing_hashes

# Handle incoming photo
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = await update.message.photo[-1].get_file()
        file_path = await photo.download_to_drive()
        img = Image.open(file_path)

        img_hash = imagehash.average_hash(img)

        if is_duplicate(img_hash):
            await update.message.reply_text("🟡 Bu rasm ilgari yuborilgan.")
        else:
            save_hash(img_hash)
            await update.message.reply_text("🆕 Yangi rasm. Xotiraga saqlandi.")

        os.remove(file_path)

    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text("❌ Rasmni tekshirishda muammo bo‘ldi.")

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
