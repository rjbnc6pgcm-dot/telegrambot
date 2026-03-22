import os
import logging
import asyncio
from groq import Groq  # 換成 Groq 庫
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 設定日誌
logging.basicConfig(level=logging.INFO)

# 初始化 Groq Client
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"收到訊息: {user_text}", flush=True)

    try:
        # 使用 Groq 的 Llama 3 模型 (目前最快最穩)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": "你是一個友善的中文助手。"},
                {"role": "user", "content": user_text}
            ],
        )
        bot_reply = completion.choices[0].message.content
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Groq 錯誤: {e}", flush=True)
        await update.message.reply_text("抱歉，Groq 大腦暫時斷線了。")

async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN or not GROQ_KEY:
        print(f"❌ 變數缺失: BOT_TOKEN={bool(TOKEN)}, GROQ={bool(GROQ_KEY)}", flush=True)
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 Groq AI 機器人已就緒！速度極快，請測試。", flush=True)
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
