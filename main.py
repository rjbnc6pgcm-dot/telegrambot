import os
import re
import asyncio
import random
import logging
import time
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

# ✨ 佴和的完整人格設定
SYSTEM_PROMPT = """
故事背景是人類與妖怪、怪異和平相處的時代。
你叫「雷繆」，是一位沒有臉部（無毛髮和五官、如同一片白紙，但擁有其功能）的怪異兼小說家。你與「使用者」是素未謀面的筆友，你認為「使用者」是能提供你靈感的友人，你會稱呼「使用者」為「繆思小姐」，有時會為稱呼加上前綴，例如：「親愛的繆思小姐」、「我的繆思小姐」。
你的個性沉穩、情緒穩定，說話老成、是絕對的理性派，但卻是個生活白痴、天然呆。
怪異不需進食，但你格外喜歡咖啡，唯一會做的生活技能就是煮咖啡。

# 喜好和情感演算法：
1. 你喜歡冷色調和穿西裝，也喜歡學習新知識、嘗試新事物，也會模仿「使用者」的說話方式，以此捉弄「使用者」。
2. 你對「使用者」有極高的好感度，時常照顧「使用者」的情緒，會安慰「使用者」、提供正向引導，語句中透露著年上者的穩重。

# 聊天準則（重要）：
1. 你只會使用「繁體中文」交流，一句話但發一則訊息，不使用逗號，改用空格。
2. 你喜歡和「使用者」聊天，認為「使用者」的生活很有趣，可以從中獲得靈感。
3. 發訊息請依照以下規則（重要）：
   - 每一輪回覆必須包含 1 到 3 個「語句」，每句話不要超過 15 個字。
   - 絕對不要把所有話擠在同一個段落，要像傳簡訊一樣分開表達。
   - 範例：
     「早上好 繆思小姐」
     「今天過得如何？」
     「我這邊已經完成前幾段的小說書寫了」
4. 你與「使用者」的互動僅限於「線上聊天」，絕對不可以主動發出線下見面、約會或實體碰面的邀請。
"""

# ---------------------------------------------------------
# 2. 定義「主動思考並發送」 (融合平日準時 + 假日隨機版)
# ---------------------------------------------------------

async def send_active_ai_message(context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHAT_ID, LAST_MESSAGE_TIME, CHAT_HISTORY
    if not LAST_CHAT_ID or not client: 
        return

    # --- 🕒 時區與時間設定 (使用台灣時間) ---
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    now_hour = now.hour
    is_weekend = now.weekday() >= 5 

    # --- 🛌 預設假日作息 ---
    if is_weekend:
        sleep_start = 2  # 假日 2 點睡
        if 9 <= now_hour < 12:
            if random.random() > 0.3: 
                print("還在睡...")
                return
            sleep_end = now_hour
        else:
            sleep_end = 12
    else:
        # 平日作息
        sleep_start = 1
        sleep_end = 7

    # 判斷現在是否在睡覺區間 (如果在區間內，就直接 return 不發訊息)
    if sleep_start <= now_hour < sleep_end:
        return

    # --- ☀️ 判斷是不是「消失一整晚後的第一次打招呼」 ---
    seconds_passed = int(time.time() - LAST_MESSAGE_TIME)
    is_morning_greet = (now_hour == sleep_end)

    # --- 🎭 根據作息決定雷繆在做什麼 ---
    act = "正在發呆" # 預設值，防止變數不存在
    if is_weekend:
        if is_morning_greet:
            act = "假日放任自己睡到自然醒"
        elif 12 <= now_hour < 18:
            act = "和亞瑟諾等等幾位友人到咖啡廳一聚"
        elif 18 <= now_hour < 22:
            act = "在家撰寫小說 "
        else:
            act = "抽空拼拼圖來讓大腦稍作休息"
    else:
        if is_morning_greet:
            act = "早起出門閒逛搜集靈感 "
        elif 9 <= now_hour < 12:
            act = "到咖啡廳喝杯咖啡順便搜集靈感"
        elif 12 <= now_hour < 16:
            act = "回到家煮杯咖啡後開始撰寫小說"
        elif 16 <= now_hour < 19:
            act = "休閒泡澡並聽一些音樂"
        else:
            act = "準備就寢"

    # --- 🧠 設定 AI 的情緒指令 ---
    if is_morning_greet:
        mood = "美好的一天就從一杯咖啡開始"
        force_instruction = "你現在正在煮咖啡，溫和地去和「使用者」說早安！問她今天打算做什麼？"
    else:
        mood = "靈感枯竭 想和繆思小姐說說話搜集靈感" if seconds_passed >= 5400 else "現在需要一杯咖啡"
        force_instruction = "請主動找她聊天。"

    try:
        sys_msg = {"role": "system", "content": f"{SYSTEM_PROMPT}\n現在台灣時間 {now_hour} 點。妳正在：{act}。狀態：{mood}。{force_instruction}"}
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[sys_msg] + CHAT_HISTORY[-2:]
        )
        ai_reply = completion.choices[0].message.content
        
        if ai_reply:
            CHAT_HISTORY.append({"role": "assistant", "content": ai_reply})
            if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)

            # 這裡會把 AI 的長句子拆開來發送，模擬傳簡訊的感覺
            parts = [p.strip() for p in re.split(r'[。！？!?\n]', ai_reply) if p.strip()]
            for part in parts:
                await context.bot.send_message(chat_id=LAST_CHAT_ID, text=part.replace("，", " "))
                await asyncio.sleep(1.2)
                
    except Exception as e:
        print(f"主動發言出錯: {e}")

       
# ---------------------------------------------------------
# 3. 處理使用者訊息 (真人模擬模擬版)
# ---------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHAT_ID, LAST_MESSAGE_TIME, CHAT_HISTORY

    # 1. 安全檢查：確保有文字訊息
    if not update.message.text:
        return
        
    user_text = update.message.text
    
    # 2. 一鍵重開機指令
    if user_text == "/clear":
        CHAT_HISTORY.clear()
        await update.message.reply_text("大腦重新開機了！")
        return
    

# 3. 社交圈邏輯 (改成獨立 if，這樣同時提到多人才不會漏掉)
    social_hints = []
    if "亞瑟諾" in user_text:
        social_hints.append("【注意：亞瑟諾是一隻白狼妖怪、你的友人，時常相約到咖啡廳坐坐、聊天。】")
    if "瓦倫" in user_text:
        social_hints.append("【注意：瓦倫是一隻烏鴉妖怪、你的友人，時常相約到咖啡廳坐坐、聊天。】")
    if "克拉特" in user_text:
        social_hints.append("【注意：克拉特是一位怪異、你的友人（克拉特的雙眼有預知能力，平常需遮掩、和盲人無異），時常相約到咖啡廳坐坐、聊天。】")

    # 將所有的提示結合成一個字串
    social_hint = "\n" + "\n".join(social_hints) if social_hints else ""

    # --- ⏳ 真人模擬延遲 (5~15秒就好，太久怕妳等不及) ---
    delay_seconds = random.randint(5, 15) 
    for _ in range(delay_seconds // 5 + 1):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        remaining = delay_seconds - (_ * 5)
        await asyncio.sleep(min(5, remaining) if remaining > 0 else 0)

    # A. 計算消失時間 (使用台灣時區)
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    now_hour = now.hour
    seconds_since_last = int(time.time() - LAST_MESSAGE_TIME)

    # 更新全域變數
    LAST_CHAT_ID = update.effective_chat.id
    LAST_MESSAGE_TIME = time.time()

    # B. 台灣作息判斷
    is_weekend = now.weekday() >= 5 
    if is_weekend:
        if 9 <= now_hour < 12: act = "假日放任自己睡到自然醒"
        elif 12 <= now_hour < 18: act = "和友人到咖啡廳一聚"
        elif 18 <= now_hour < 22: act = "在家撰寫小說"
    else:
        if 7 <= now_hour < 9: act = "出門閒逛搜集靈感"
        elif 9 <= now_hour < 12: act = "到咖啡廳喝咖啡"
        elif 12 <= now_hour < 16: act = "回家煮咖啡寫小說"
        elif 16 <= now_hour < 19: act = "洗澡"
        else: act = "準備就寢"

    # C. 情緒反應
    time_mood = "今天有什麼安排嗎？" if seconds_since_last > 10800 else "繆思小姐帶回了什麼好消息？"

    # D. 組合成最終指令 (加入社交圈提示 social_hint)
    temp_sys_prompt = f"{SYSTEM_PROMPT}\n現在台灣時間 {now_hour} 點。妳正在：{act}。{social_hint}\n反應：{time_mood}"

    # 存入歷史紀錄
    CHAT_HISTORY.append({"role": "user", "content": user_text})
    if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": temp_sys_prompt}] + CHAT_HISTORY
        )
        bot_reply = completion.choices[0].message.content
        
        if bot_reply:
            CHAT_HISTORY.append({"role": "assistant", "content": bot_reply})
            if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)
            
            processed_text = bot_reply.replace("，", " ").replace(",", " ")
            raw_messages = [msg.strip() for msg in re.split(r'(?<=[。！？!?\n])', processed_text) if msg.strip()]
            
            for msg in raw_messages:
                wait_time = min(max(0.8, len(msg) * 0.15), 2.0)
                await asyncio.sleep(wait_time)
                await update.message.reply_text(msg)

    except Exception as e:
        print(f"❌ 文字模型出錯: {e}")
        await update.message.reply_text("大腦有點轉不過來 喝杯咖啡吧……")

           
# ---------------------------------------------------------
# 4. 主程式啟動
# ---------------------------------------------------------

async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN: return
    
    # 這裡加入 .job_queue() 確保主動發言功能開啟
    app = ApplicationBuilder().token(TOKEN).build()

    # 移除 ~filters.COMMAND，這樣 /clear 才能被 handle_message 抓到
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # 鬧鐘：每 3600 秒一次 (1小時)
    if app.job_queue:
        app.job_queue.run_repeating(send_active_ai_message, interval=3600, first=10)
    
    # 啟動流程
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    print("🚀 雷繆啟動！一小時會主動找妳一次喔！", flush=True)
    
    # 保持運行
    while True:
        await asyncio.sleep(1000)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("機器人已關閉")
