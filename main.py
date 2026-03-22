import os
import logging
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. 設定日誌
logging.basicConfig(level=logging.INFO)

# 2. 設定 Gemini
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # 使用快速穩定的 Flash 版本

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"收到來自 {update.effective_user.first_name} 的訊息: {user_text}", flush=True)

    try:
        # 讓 Gemini 思考並產生回覆
        response = model.generate_content(user_text)
        bot_reply = response.text
        
        # 把 AI 的回答傳回給 Telegram
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Gemini 發生錯誤: {e}", flush=True)
        await update.message.reply_text("抱歉，我的大腦斷線了，請稍後再試。")

async def main():
    # 讀取 Telegram Token
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN or not GEMINI_KEY:
        print("❌ 錯誤：找不到 BOT_TOKEN 或 GEMINI_API_KEY，請檢查 Railway 變數！", flush=True)
        return

    # 建立機器人
    app = ApplicationBuilder().token(TOKEN).build()
    
    # 處理所有文字訊息
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 Gemini 機器人已就緒！", flush=True)
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
