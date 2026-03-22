import os
import logging
import asyncio
from google import genai  # 使用新的 google-genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 設定日誌
logging.basicConfig(level=logging.INFO)

# 初始化 Gemini Client
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"收到來自 {update.effective_user.first_name} 的訊息: {user_text}", flush=True)

    try:
        # 使用新版 SDK 的 generate 語法
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=user_text
        )
        bot_reply = response.text
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Gemini 錯誤: {e}", flush=True)
        await update.message.reply_text("抱歉，我現在無法思考，請稍後再試。")

async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    
    # 再次檢查變數是否齊全
    if not TOKEN or not GEMINI_KEY:
        print(f"❌ 變數缺失檢查: BOT_TOKEN={bool(TOKEN)}, GEMINI={bool(GEMINI_KEY)}", flush=True)
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 最新版 Gemini 機器人啟動中...", flush=True)
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
