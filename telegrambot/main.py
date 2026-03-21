from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個有點調皮的聊天助手"},
            {"role": "user", "content": user_msg}
        ]
    )

    await update.message.reply_text(response['choices'][0]['message']['content'])

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, reply))
app.run_polling()
