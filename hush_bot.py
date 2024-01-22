import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

FEEDBACK_MESSAGE = range(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class UserInfo(Base):
    __tablename__ = 'user_info'

    id = Column(Integer, primary_key=True)
    username = Column(String(255))
    chat_id = Column(Integer, unique=True)


class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True)
    username = Column(String(255))
    chat_id = Column(Integer)
    message = Column(Text)


def save_user_info(username, chat_id):
    session = Session()
    try:
        if user := session.query(UserInfo).filter_by(chat_id=chat_id).first():
            user.username = username
        else:
            session.add(UserInfo(username=username, chat_id=chat_id))
        session.commit()
    finally:
        session.close()


def save_feedback(username, chat_id, message):
    session = Session()
    try:
        session.add(Feedback(username=username, chat_id=chat_id, message=message))
        session.commit()
    finally:
        session.close()


def get_chat_id_from_username(username):
    session = Session()
    try:
        if user := session.query(UserInfo).filter_by(username=username).first():
            return user.chat_id
        else:
            return None
    finally:
        session.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    if username:
        save_user_info(username, user_id)

    await update.message.reply_text(f"Hello! You can now send me another user's ID and I will HUSH them.")


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send your feedback.")
    return FEEDBACK_MESSAGE


async def feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.from_user.id
    username = update.message.from_user.username
    message = update.message.text

    if username:
        save_user_info(username, chat_id)
    save_feedback(username, chat_id, message)

    await update.message.reply_text("Thank you for your feedback.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def hush_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    if username:
        save_user_info(username, user_id)

    target_username = update.message.text
    if target_username[0] == '@':
        target_username = target_username[1:]
    target_chat_id = get_chat_id_from_username(target_username)
    if target_chat_id:
        await context.bot.send_message(chat_id=target_chat_id, text="HUSH")
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
