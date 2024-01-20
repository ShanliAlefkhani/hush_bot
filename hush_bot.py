import os
from dotenv import load_dotenv
import psycopg2
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def save_user_info(username, chat_id):
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        cursor = connection.cursor()

        username = username.lower()

        cursor.execute(
            "INSERT INTO user_info (username, chat_id) VALUES (%s, %s) ON CONFLICT (username) DO UPDATE SET chat_id = "
            "EXCLUDED.chat_id",
            (username, chat_id)
        )

        connection.commit()

    finally:
        if connection:
            connection.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    save_user_info(username, user_id)

    await update.message.reply_text(f"Hello! You can now send me another user's ID and I will HUSH them.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.run_polling()
