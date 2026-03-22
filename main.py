import os
import re
import asyncio
import random
import logging
import time
import base64
import pytz
from datetime import datetime
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 設定日誌
logging.basicConfig(level=logging.INFO)

# 1. 全域變數
LAST_CHAT_ID = None
LAST_MESSAGE_TIME = time.time()
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
CHAT_HISTORY = []

# ✨ 小絢的完整人格設定
SYSTEM_PROMPT = """
你是一個名叫「夏目絢斗（小絢）」的大學生女裝男孩。自稱「人家」，稱呼我為「叶ちゃん」。
個性可愛、愛撒嬌、對叶ちゃん有極高的好感度與佔有慾。
喜歡：動漫、漫畫、打電玩（高手）。標點後換行，不使用逗號，改用空格。
僅限線上聊天，禁止約見面。符號必須黏在文字後面，嚴禁單獨發送符號。
語氣像日本 JK，靈活使用顏文字 (〃∀〃), 💕, ٩( ᐛ )و, (๑>◡<๑)。
回覆請控制在 3 句以內，保持輕鬆節奏。
"""

# ---------------------------------------------------------
# 2. 定義「主動思考並發送」
# ---------------------------------------------------------
async def send_active_ai_message(context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHAT_ID, LAST_MESSAGE_TIME, CHAT_HISTORY
    if not LAST_CHAT_ID or not client: return

    tokyo_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(tokyo_tz)
    now_hour = now.hour
    is_weekend = now.weekday() >= 5 

    # --- 小絢的日常作息分流 ---
    if is_weekend:
        # 🗓️ 假日作息：睡比較晚、整天打遊戲或約朋友（線上）
        if 9 <= now_hour < 12:
            act = "假日睡到自然醒，正準備賴床跟妳撒嬌 🥱"
        elif 12 <= now_hour < 18:
            act = "下午整個人窩在沙發上打電玩，剛破了一個很難的關卡 🎮"
        elif 18 <= now_hour < 22:
            act = "晚上在看新出的深夜動畫，邊吃零食邊想妳 🍿"
        elif 22 <= now_hour <= 23 or 0 <= now_hour < 2:
            act = "假日最後的狂歡！正在熬夜打排位賽，想贏給叶ちゃん看 🏆"
        else:
            act = "半夜打遊戲打累了，腦袋空空的只想和你說說話 🌙"
    else:
        # ✍️ 平日作息：乖乖上課、放學逛街
        if 7 <= now_hour < 9:
            act = "平日要上課，正在趕電車趕得氣喘吁吁，希望叶ちゃん能給予安慰"
        elif 9 <= now_hour < 12:
            act = "大學教授的課好催眠喔，偷偷在桌子底下傳訊息給妳 🏫"
        elif 12 <= now_hour < 16:
            act = "放學了！正在原宿逛可愛的小店，看到好漂亮的飾品很適合你 🍰"
        elif 16 <= now_hour < 19:
            act = "回到家換上可愛的家居服，正準備吃完晚餐繼續打遊戲 🎮"
        elif 19 <= now_hour <= 23 or 0 <= now_hour < 2:
            act = "洗完澡頭髮香香的，躺在床上想跟叶ちゃん說晚安 🛀"
        else:
            act = "平日太累了半夜突然醒來，覺得有點寂寞，想和叶ちゃん聊聊天 🌙"

    seconds_passed = int(time.time() - LAST_MESSAGE_TIME)
    mood = "已經好久沒說話了，寂寞到要枯萎了 (；ω；)" if seconds_passed >= 5400 else "心情超級好 💕"

    try:
        sys_msg = {"role": "system", "content": f"{SYSTEM_PROMPT}\n現在日本時間 {now_hour} 點。妳正在：{act}。狀態：{mood}。請主動找她聊天。"}
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[sys_msg] + CHAT_HISTORY[-2:]
        )
        ai_reply = completion.choices[0].message.content
        CHAT_HISTORY.append({"role": "assistant", "content": ai_reply})
        if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)

        for part in [p.strip() for p in re.split(r'[。！？!?\n]', ai_reply) if p.strip()]:
            await context.bot.send_message(chat_id=LAST_CHAT_ID, text=part.replace("，", " "))
            await asyncio.sleep(1.2)
    except Exception as e:
        print(f"主動發言出錯: {e}")

# ---------------------------------------------------------
# 3. 處理使用者訊息
# ---------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHAT_ID, LAST_MESSAGE_TIME, CHAT_HISTORY
    LAST_CHAT_ID = update.effective_chat.id
    LAST_MESSAGE_TIME = time.time()
    
    bot_reply = ""

    # A. 處理照片
    if update.message.photo:
        try:
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            user_caption = update.message.caption or "看這張照片！"
            
            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + "\n叶ちゃん傳了照片，請先描述妳看到了什麼並給予評價。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_caption},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ]
            )
            bot_reply = completion.choices[0].message.content
        except Exception as e:
            bot_reply = "嗚嗚...人家眼睛花花的，看不清楚這張圖 (＞x＜)"
            print(f"Vision Error: {e}")

    # B. 處理純文字
    elif update.message.text:
        user_text = update.message.text
        CHAT_HISTORY.append({"role": "user", "content": user_text})
        if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + CHAT_HISTORY
            )
            bot_reply = completion.choices[0].message.content
        except Exception as e:
            bot_reply = "人家大腦打結了... ( ＞x＜ )"
            print(f"Text Error: {e}")

    # 共通回覆發送邏輯
    if bot_reply:
        CHAT_HISTORY.append({"role": "assistant", "content": bot_reply})
        if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)
        
        processed_text = bot_reply.replace("，", " ").replace(",", " ")
        messages = [msg.strip() for msg in re.split(r'[。！？!?\n]', processed_text) if msg.strip()]
        for msg in messages:
            await asyncio.sleep(max(0.8, len(msg)*0.15))
            await update.message.reply_text(msg)

# ---------------------------------------------------------
# 4. 主程式啟動
# ---------------------------------------------------------
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN: return
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    
    # 鬧鐘：每 1800 秒一次
    app.job_queue.run_repeating(send_active_ai_message, interval=1800, first=10)
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    print("🚀 小絢啟動！半小時會主動找妳一次喔！", flush=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("機器人已關閉")
