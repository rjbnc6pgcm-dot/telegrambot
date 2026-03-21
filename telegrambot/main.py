import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI  # 使用非同步 Client

# 設定日誌，方便在 GitHub Actions 或伺服器上排錯
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 從環境變數讀取金鑰 (GitHub Secrets 設定)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 初始化非同步 OpenAI 客戶端
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理使用者訊息並呼叫 OpenAI API"""
    
    # 安全檢查：確保訊息存在且包含文字
    if not update.message or not update.message.text:
        return

    user_msg = update.message.text

    try:
        # 使用 await 呼叫 OpenAI，不會阻塞其他使用者
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一個有點調皮的聊天助手"},
                {"role": "user", "content": user_msg}
            ]
        )

        # 新版 SDK 取值方式：使用屬性存取 (.choices) 而非字典 (['choices'])
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)

    except Exception as e:
        logging.error(f"Error calling OpenAI: {e}")
        await update.message.reply_text("哎呀，我的大腦斷線了，請稍後再試！")

async def main():
    """啟動機器人"""
    if not BOT_TOKEN or not OPENAI_API_KEY:
        print("錯誤：請設定環境變數 BOT_TOKEN 和 OPENAI_API_KEY")
        return

    # 建立 Application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 註冊處理器：只處理文字訊息，排除指令
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reply))

    print("機器人運行中...")
    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()  # Keep running

if __name__ == "__main__":
    main()
