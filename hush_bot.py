import os
from dotenv import load_dotenv
import psycopg2
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

FEEDBACK_MESSAGE = range(1)


def save_user_info(username, chat_id):
    connection = None
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
            "INSERT INTO user_info (username, chat_id) VALUES (%s, %s) ON CONFLICT (chat_id) DO UPDATE SET username = "
            "EXCLUDED.username",
            (username, chat_id)
        )

        connection.commit()

    finally:
        if connection:
            connection.close()


def save_feedback(username, message_text):
    connection = None
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO feedback (username, message_text) VALUES (%s, %s)",
            (username, message_text)
        )

        connection.commit()

    finally:
        if connection:
            connection.close()


def get_user_id_from_username(username):
    connection = None
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

        cursor.execute("SELECT chat_id FROM user_info WHERE username = %s", (username,))
        result = cursor.fetchone()

        return result[0] if result else None

    finally:
        if connection:
            connection.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    save_user_info(username, user_id)

    await update.message.reply_text(f"Hello! You can now send me another user's ID and I will HUSH them.")


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send your feedback.")
    return FEEDBACK_MESSAGE


async def feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    message_text = update.message.text
    save_feedback(username, message_text)

    await update.message.reply_text("Thank you for your feedback.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def hush_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target_username = update.message.text
    if target_username[0] == '@':
        target_username = target_username[1:]
    target_user_id = get_user_id_from_username(target_username)
    if target_user_id:
        await context.bot.send_message(chat_id=target_user_id, text="HUSH")
        await update.message.reply_text(f"Message sent to user with ID {target_username}.")
        return
    await update.message.reply_text("This user has not started the bot yet! You can share the bot with them.")


if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('feedback', feedback)],
        fallbacks=[CommandHandler("cancel", cancel)],
        states={
            FEEDBACK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_message)],
        },
    ))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), hush_user))

    app.run_polling()
