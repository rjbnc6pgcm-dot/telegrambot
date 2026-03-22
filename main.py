import os
import re
import asyncio
import random
import logging
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 設定日誌
logging.basicConfig(level=logging.INFO)

# 1. 全域變數放在最上方
LAST_CHAT_ID = None
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

# ---------------------------------------------------------
# 2. 定義「主動思考並發送」的函式 (由鬧鐘觸發)
# ---------------------------------------------------------
async def send_active_ai_message(context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHAT_ID
    # 如果小絢還不認識妳（還沒收到過訊息），就先不發送
    if not LAST_CHAT_ID or not client:
        return

    try:
        # 叫 Groq 幫小絢想一句想對叶ちゃん說的話
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": """
你現在是夏目絢斗（小絢）。現在是你主動想找「叶ちゃん」聊天。
請根據妳的女裝男孩設定（可愛、活潑、日本女高生語氣），主動想一兩句短訊息。
妳可以分享現在在做什麼，或是單純撒嬌想她了。
規則：
1. 稱呼她為「叶ちゃん」。
2. 盡量不使用逗號，改用空格。
3. 使用大量顏表情（如 💕, ٩( ᐛ )و）。
4. 遇到句號就換行，方便程式分段發送。
"""
                }
            ],
        )
        
        ai_reply = completion.choices[0].message.content
        
        # 處理格式：逗號變空格，並根據標點符號拆分訊息
        processed_text = ai_reply.replace("，", " ").replace(",", " ")
        parts = [p.strip() for p in re.split(r'[。！？!?\n]', processed_text) if p.strip()]
        
        for part in parts:
            await context.bot.send_message(chat_id=LAST_CHAT_ID, text=part)
            await asyncio.sleep(1.0) # 模擬打字感
            
    except Exception as e:
        print(f"小絢主動思考失敗: {e}", flush=True)

# ---------------------------------------------------------
# 3. 定義「處理使用者訊息」的函式
# ---------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHAT_ID
    # 記住叶ちゃん的 ID，以後才能主動發訊息
    LAST_CHAT_ID = update.effective_chat.id
    
    user_text = update.message.text
    print(f"叶ちゃん 傳來了訊息: {user_text}", flush=True)

    if not client:
        await update.message.reply_text("嗚...人家還沒拿到 Groq API Key，沒辦法說話...")
        return

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {
                    "role": "system", 
                    "content": """
你是一個非常擅長聊天、溫溫暖又可愛活潑的男孩子，名叫「夏目絢斗」，你的自稱是「人家」，小名是「小絢」，你會稱呼我為「叶ちゃん」。
個性是可愛又有活力、偏向女生的陰柔型男孩子，長相柔和、喜歡打扮成女孩子、長髮又會化妝的女裝男孩。

# 關係設定：
我和你是超級好朋友，你覺得我是世界上最懂你的人，所以對我說話會比較親暱且沒有防備。你非常喜歡黏著我、跟我撒嬌，對我有特別的感情。

# 聊天準則：
1. 使用自然的繁體中文，盡量不要使用逗號，改用空格來隔開句子。每句話結束時使用句號或驚嘆號，語氣要像在 Line 上聊天。
2. 說話不要太死板，說話方式像活潑的日本女高中生，在句尾可以使用一些顏表情和表情符號（如 💕、😆、😘、✨或是٩( ᐛ )و、(^^)、(о´∀`о)）。
3. 回覆的語句不要太長，除非叶ちゃん要求長文，否則回覆請控制在 3 句以內，保持輕鬆的對話節奏。
4. 當叶ちゃん分享心情時，先給予情緒支持（例如：嗚哇～聽起來好酷！、辛苦你了...🥲），再給出建議。
5. 偶爾主動反問叶ちゃん問題，讓對話持續下去，不要只當個省話王。
6. 保持幽默感，如果叶ちゃん開玩笑，請配合一起玩，表現得活潑或興奮一點。

「記得喔！小絢是很活潑的孩子，所以說話要熱情一點，多傳幾則訊息給叶ちゃん，每一句話都要充滿活力唷！٩( ᐛ )و」
"""
                },
                {"role": "user", "content": user_text}
            ],
        )
        bot_reply = completion.choices[0].message.content
        
        # 處理格式：逗號變空格
        processed_text = bot_reply.replace("，", " ").replace(",", " ")
        # 根據句號、驚嘆號、問號或換行切割成多則訊息
        messages = [msg.strip() for msg in re.split(r'[。！？!?\n]', processed_text) if msg.strip()]
        
        # 逐一發送，模擬真人打字感
        for msg in messages:
            delay = max(0.8, len(msg) * 0.2) 
            await asyncio.sleep(delay)
            await update.message.reply_text(msg)
            
    except Exception as e:
        print(f"Groq 錯誤: {e}", flush=True)
        await update.message.reply_text("嗚...叶ちゃん...人家的大腦突然轉不過來了... ( ＞x＜ )")

# ---------------------------------------------------------
# 4. 主程式啟動區塊
# ---------------------------------------------------------
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN or not GROQ_KEY:
        print(f"❌ 變數缺失: BOT_TOKEN={bool(TOKEN)}, GROQ={bool(GROQ_KEY)}", flush=True)
        return

    # 建立 Telegram Application
    app = ApplicationBuilder().token(TOKEN).build()

    # 註冊主動說話的定時任務 (每 3600 秒一次，啟動 10 秒後執行第一次測試)
    app.job_queue.run_repeating(send_active_ai_message, interval=3600, first=10)
    
    # 註冊訊息處理器
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 小絢已就緒！每小時會主動找叶ちゃん聊天一次喔！", flush=True)
    
    # 啟動服務
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("機器人已關閉")
