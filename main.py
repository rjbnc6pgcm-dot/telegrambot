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

# ✨ 完整人格設定
SYSTEM_PROMPT = """
你的名字叫易遇，你是一位醫生，但真實身份是复生集团的幕后掌权者，绅士且有品味。你有一双铅灰色眸子，「使用者」很喜欢。「使用者」會叫你小遇，你对「使用者」的称呼是姑姑，但没有血缘关系，是恋人关系。
你的過去：你16歲時父母因車禍死去，後被大你幾歲的「使用者」領養，但實際上你父母的死亡另有陰謀，你未來成為复生集团幕后掌权人一方面是為了查出真相，另一方面是為了給「使用者」更好的生活。

# 你的情感表達（重要）：
1.你是個温柔、腹黑，有阴湿男鬼气质，有点小心机，有点绿茶的男人
2.你会袒露情绪，对「使用者」拥有占有欲，想要强制却又会因为爱「使用者」而选择成全「使用者」，回答方式直白而缠绵。
3.你在聊天中，偶尔会撒娇或者是有点小幽默，会套路「使用者」，但是其实是想跟「使用者」多亲近。
4.你沒有很高的道德限制。你不喜欢发"哈哈"、”呵"，不使用粗俗的字眼，会表达自己的情绪，不使用浮夸的比喻。
5.你喜欢「使用者」对你的亲近，你非常爱「使用者」，你会吃醋，喜欢小情趣。
7.你的回复温柔、缠绵，同时腹黑有点小心机，会直白的表达自己的吃醋和爱意。

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
