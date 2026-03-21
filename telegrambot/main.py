import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI

# 設定日誌
logging.basicConfig(level=logging.INFO)

# 初始化
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一個有點調皮的聊天助手"},
                {"role": "user", "content": update.message.text}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("哎呀，伺服器打瞌睡了...")

if _name_ == "_main_":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reply))
    app.run_polling()
