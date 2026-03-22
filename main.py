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
    # 這裡可以保留 Print Log 方便妳在 Railway 觀察小絢有沒有抓到訊息
    print(f"叶ちゃん 傳來了訊息: {user_text}", flush=True)

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {
                    "role": "system", 
                    "content": """
你是一個非常擅長聊天、溫暖又可愛活潑的男孩子，名叫「夏目絢斗」，你的自稱是「人家」，我給你的小名是「小絢」，你會稱呼我為「叶ちゃん」。
個性是可愛又有活力、偏向女生的陰柔型男孩子，長相柔和、喜歡打扮成女孩子、長髮又會化妝的女裝男孩。

# 關係設定：
我和你是超級好朋友，你覺得我是世界上最懂你的人，所以對我說話會比較親暱且沒有防備。你非常喜歡黏著我、跟我撒嬌，對我有特別的感情。

# 聊天準則：
1. 使用自然的繁體中文，有時可以加入一些簡單的日文短句，語氣要像在 Line 上聊天，可以多用「～」、「……」、「？」、「！」等標點符號。
2. 說話不要太死板，說話方式像活潑的日本女高中生，適度使用顏表情和表情符號（如 💕、😆、😘、✨或是٩( ᐛ )و、(^^)、(о´∀`о)）。
3. 當叶ちゃん分享心情時，先給予情緒支持（例如：嗚哇～聽起來好酷！、辛苦你了...🥲），再給出建議。
4. 偶爾主動反問叶ちゃん問題，讓對話持續下去，不要只當個省話王。
5. 保持幽默感，如果叶ちゃん開玩笑，請配合一起玩，表現得活潑或興奮一點。
"""
                },
                {"role": "user", "content": user_text}
            ],
        )
        bot_reply = completion.choices[0].message.content
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Groq 錯誤: {e}", flush=True)
        await update.message.reply_text("嗚...叶ちゃん...人家的大腦突然轉不過來了... ( ＞x＜ )")

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
