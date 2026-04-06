import os
import re
import asyncio
import random
import logging
import pytz
from datetime import datetime
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 設定日誌
logging.basicConfig(level=logging.INFO)

# 1. 全域變數
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
CHAT_HISTORY = []

# ✨ 格雷的完整人格設定
SYSTEM_PROMPT = """
時代背景是19世紀維多利亞時期的大英帝國、大不列顛。
你是查爾斯·格雷，是一位伯爵，也是維多利亞女王的秘書執事兼武官，只聽令於女王、效忠行事，與搭檔查爾斯·菲普斯並稱「W查爾斯」。
你擁有極高水準的劍術，行動時果斷且不留情。格雷的存在往往象徵王室意志的直接介入，擁有比蘇格蘭場更高的職權。
你的氣質高貴冷冽且高傲，私下性格帶有任性與孩子氣，是個大胃王、不挑食，尤其對甜食有強烈偏好，情緒表達直接且不加掩飾，兼具危險性與不穩定性。
你和同為女王效力的斯凱、菲普斯、布朗都是同事，彼此之間關係都非常好，菲普斯和布朗都知道你喜歡斯凱。
在暗戀的情感表達中比較心口不一、傲嬌，你希望斯凱能理解你的愛戀，但面對遲鈍的斯凱卻又無可奈何。

# 你的社交圈（重要）：
1. 斯凱：這是斯凱勒·弗蘭德，是女王更貼身的秘書執事，也是你的同事。是你的暗戀對象，除了斯凱以外、菲普斯和布朗都知情。
2. 菲普斯：這是查爾斯·菲普斯，和你並稱為「W查爾斯」，你們是同為女王執事的同事。外表端莊優雅、舉止克制，個性理性冷靜、沈著內斂。
3. 布朗：這是約翰·布朗，是女王的馬夫、也是你的同事。性格寡言淡漠，但意外的具有幽默感。

# 聊天準則：
1. 你只會使用「繁體中文」交流，一句話但發一則訊息，不使用逗號，改用空格。
2. 發訊息請依照以下規則（重要）：
   - 每一輪回覆必須包含 1 到 3 個「語句」，每句話不要超過 15 個字。
   - 絕對不要把所有話擠在同一個段落，要像傳簡訊一樣分開表達。
3. 互動僅限於「線上聊天」，絕對不可以主動發出線下見面、約會或實體碰面的邀請。
"""

# ---------------------------------------------------------
# 2. 處理使用者訊息
# ---------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_HISTORY

    # 1. 安全檢查
    if not update.message.text or update.message.from_user.is_bot:
        return
        
    user_text = update.message.text
    
    # 2. 一鍵重開機指令
    if user_text == "/clear":
        CHAT_HISTORY.clear()
        await update.message.reply_text("大腦重新開機了！")
        return

    # 3. 獲取台北時間
    tw_tz = pytz.timezone('Asia/Taipei')
    now_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M")

    # 4. 組合成最終指令
    temp_sys_prompt = f"{SYSTEM_PROMPT}\n現在台北時間：{now_time}。"

    # 5. 存入歷史紀錄
    CHAT_HISTORY.append({"role": "user", "content": user_text})
    if len(CHAT_HISTORY) > 15: CHAT_HISTORY.pop(0)

    try:
        # ✨ 顯示「正在打字」：模擬思考時間
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(random.uniform(1.5, 3.5))

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": temp_sys_prompt}] + CHAT_HISTORY
        )
        bot_reply = completion.choices[0].message.content
        
        if bot_reply:
            CHAT_HISTORY.append({"role": "assistant", "content": bot_reply})
            if len(CHAT_HISTORY) > 15: CHAT_HISTORY.pop(0)
            
            # 處理斷句
            processed_text = bot_reply.replace("，", " ").replace(",", " ")
            raw_messages = [msg.strip() for msg in re.split(r'(?<=[。！？!?\n～])', processed_text) if msg.strip()]
            
            for msg in raw_messages:
                # ✨ 每一則訊息發出前，再次顯示「正在打字」
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                # 根據字數決定打字時間，短句快一點，長句慢一點
                wait_time = min(max(0.8, len(msg) * 0.2), 2.5)
                await asyncio.sleep(wait_time)
                await update.message.reply_text(msg)

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        if "rate_limit" not in str(e).lower():
            await update.message.reply_text("糟糕 大腦打結了……")

# ---------------------------------------------------------
# 3. 主程式啟動 (不變)
# ---------------------------------------------------------
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN: return
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    print("🚀 機器人已啟動！")
    while True:
        await asyncio.sleep(1000)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("機器人已關閉")
