import logging
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ContextTypes,  MessageHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id = update.effective_chat.id, text=update.message.text
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)



if __name__ == "__main__":
    application = (
        ApplicationBuilder()
        .token("6610669277:AAFNx0EHD-S4Cr5mahInjAkQiLSV2NULtAI")
        .build()
    )

    caps_handler = CommandHandler('caps', caps)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND),echo)
    # ~ user for ignoring Commands.
    # & is like AND Operator 
    start_handler = CommandHandler("start", start)

    application.add_handler(start_handler)
    application.add_handler(echo_handler) 
    application.add_handler(caps_handler)

    application.run_polling()
