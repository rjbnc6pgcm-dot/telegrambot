import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 設定日誌
logging.basicConfig(level=logging.INFO)

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"收到訊息: {user_text}", flush=True)
    
    # 這裡可以加入 AI 邏輯 (例如之前的 OpenAI 或 Gemini 代碼)
    # 目前先做簡單的回覆測試
    await update.message.reply_text(f"機器人已上線！你說了：{user_text}")

async def main():
    # 改回從環境變數讀取，不要寫死在程式碼裡
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        print("錯誤：找不到 BOT_TOKEN 變數！", flush=True)
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reply))
    
    print(">>> 機器人正常啟動中...", flush=True)
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
