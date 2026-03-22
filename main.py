import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 設定最暴力的日誌
logging.basicConfig(level=logging.INFO)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"連線成功！收到：{update.message.text}")

async def main():
    # 這裡直接換成你那個測試成功的 Token (記得帶引號)
    TOKEN = "8792523156:AAGYb8NJ1FWICq0RfN0nL_gfn8jZ7kmtBE4" 
    
    print("--- 正在嘗試用硬編碼 Token 啟動 ---", flush=True)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    print(">>> 成功啟動！請在 Telegram 傳訊息測試", flush=True)
    await asyncio.Event().wait()

if _name_ == "_main_":
    asyncio.run(main())