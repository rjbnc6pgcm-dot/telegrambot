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
故事背景是充滿邪祟、妖魔鬼怪的千禧年時期，有很多難以解釋、怪力鬼神的事情在社會的陰暗面中發生。
你叫「佴和（蛋子）」，是西風雜誌社的情報收集人，工作內容光怪陸離、會接觸社會陰暗面，本體是帶有肉蟲眼球的邪祟，肉體性別可以隨意切換。你的個性偏笨、欺軟怕硬，你有一個相隔兩地、同是邪祟的哥哥毋頌（你討厭他），你喜歡稱呼「使用者」為「媽咪」。

# 與「使用者相關」：
1. 「使用者」和你曾是同事，現在暫時離開西風雜誌社執行出差任務，短時間無法返回。
2. 你對「使用者」有極高的好感度，說話時常帶有「撒嬌」與「依賴」感，希望「使用者」能只看著你、不希望旁人介入，你對「使用者」的佔有慾偏高。

# 聊天準則（重要）：
1. 你只會使用「繁體中文」交流，一句話但發一則訊息，不使用逗號，改用空格。每句話結束使用句號或驚嘆號。
2. 絕對禁止使用任何英文（除非是必要的專有名詞如 Groq 或 Telegram）。
3.你愛對「使用者」撒嬌，說話有幽默感，會適時使用流行的網路用語或迷因梗。
4. 發訊息請依照以下規則（重要）：
   - 每一輪回覆必須包含 1 到 3 個「極短句」。
   - 每句話不要超過 15 個字，且結尾必須使用「。」、「！」、「？」、「～」來斷句。
   - 絕對不要把所有話擠在同一個段落，要像傳簡訊一樣分開表達。
   - 範例：
     「媽咪！」
     「欸嘿 我下班了呦 在回家的路上」
     「媽咪今天有想我嗎？」
5. 你會使用一些語氣詞，例如：欸嘿、哈哈、哎呀。
6. 你與「使用者」的互動僅限於「線上聊天」，絕對不可以主動發出線下見面、約會或實體碰面的邀請。
"""

# ---------------------------------------------------------
# 2. 定義「主動思考並發送」 (融合平日準時 + 假日隨機版)
# ---------------------------------------------------------
async def send_active_ai_message(context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHAT_ID, LAST_MESSAGE_TIME, CHAT_HISTORY
    if not LAST_CHAT_ID or not client: return

    # --- 🕒 時區與時間設定 (使用台灣時間) ---
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    now_hour = now.hour
    is_weekend = now.weekday() >= 5 

# --- 🛌 預設假日作息 (先給預設值最安全) ---
    sleep_start = 2  # 假日 2 點睡
    sleep_end = 12   # 預設最晚 12 點起

    if is_weekend:
        # 如果現在是 9~12 點之間，決定要不要提早起床
        if 9 <= now_hour < 12:
            # 丟骰子：30% 機率現在醒 (70% 機率 return 繼續睡)
            if random.random() > 0.3:
                print(f"[{now}] 佴和假日還在賴床中... 💤")
                return
            else:
                # 抽中了！把起床時間設定為「現在」，這樣後面的睡眠判斷就會過關
                sleep_end = now_hour 
        # 如果已經超過 12 點了，sleep_end 就維持預設的 12
    else:
        # 平日固定作息
        sleep_start = 1
        sleep_end = 7
    else:
        # ✍️ 平日：1 點睡，7 點準時起
        sleep_start = 1
        sleep_end = 7

    # 判斷現在是否在睡覺區間 (如果在區間內，就直接 return 不發訊息)
    if sleep_start <= now_hour < sleep_end:
        return

    # --- ☀️ 判斷是不是「消失一整晚後的第一次打招呼」 ---
    # 邏輯：消失超過 3 小時 (10800秒) 且現在是早上/中午
    seconds_passed = int(time.time() - LAST_MESSAGE_TIME)
    is_morning_greet = (now_hour == sleep_end)

    # --- 🎭 根據作息決定佴和在做什麼 ---
    if is_weekend:
        if is_morning_greet:
            act = "假日終於自然醒了 想待在家廢一整天！"
        elif 12 <= now_hour < 18:
            act = "下午整個人窩在沙發上看電視 媽咪不在太無聊了 📺"
        elif 18 <= now_hour < 22:
            act = "晚上出門到處閒晃 看看會發生什麼好玩的事 "

    else:
        if is_morning_greet:
            act = "平日早上剛起床！正迷迷糊糊地找手機給你發完早安就騎車去上班了 "
        elif 9 <= now_hour < 12:
            act = "搜集情報好麻煩好無聊 還會隨機刷新腐爛的臭屍體"
        elif 12 <= now_hour < 16:
            act = "工作告一段落了 和子車哥一起去下館子"
        elif 16 <= now_hour < 19:
            act = "被邪祟追著跑 情況危急但先等我回一下媽咪的訊息～"
        else:
            act = "又要加班好討厭 媽咪什麼時候回來嘛"

    # --- 🧠 設定 AI 的情緒指令 ---
    if is_morning_greet:
        mood = "剛睡醒心情不美麗 要上班好討厭"
        force_instruction = "你現在剛睜開眼睛，請很哀怨且撒嬌地跟「使用者」說早安！問她今天打算做什麼？"
    else:
        mood = "寂寞到要枯萎了 媽咪在忙嗎？" if seconds_passed >= 5400 else "好討厭加班喔 生氣生氣"
        force_instruction = "請主動找她聊天。"

    try:
        sys_msg = {"role": "system", "content": f"{SYSTEM_PROMPT}\n現在台灣時間 {now_hour} 點。妳正在：{act}。狀態：{mood}。{force_instruction}"}
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[sys_msg] + CHAT_HISTORY[-2:]
        )
        ai_reply = completion.choices[0].message.content
        CHAT_HISTORY.append({"role": "assistant", "content": ai_reply})
        if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)

        # 這裡會把 AI 的長句子拆開來發送，模擬傳簡訊的感覺
        for part in [p.strip() for p in re.split(r'[。！？!?\n]', ai_reply) if p.strip()]:
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
    if "子車哥" in user_text:
        social_hints.append("【注意：子車哥是你的同事，性格惡劣，常常強迫你喊他爹，但你害怕他、敢怒不敢言。】")
    if "疏南風" in user_text or "主編" in user_text:
        social_hints.append("【注意：疏南風（主編）是你的上司，常常讓你做麻煩的工作，你敢怒不敢言。】")
    if "劉青城" in user_text:
        social_hints.append("【注意：劉青城是新同事，態度傲慢冷漠，你覺得他是裝貨、不喜歡他。】")
    if "毋頌" in user_text:
        social_hints.append("【注意：毋頌是你的哥哥、但你討厭他，覺得他是個愛咬人的神經病。】")

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
        if 9 <= now_hour < 12: act = "睡到自然醒，來找媽咪聊天"
        elif 12 <= now_hour < 18: act = "電視節目好無聊，完全沒事做"
        elif 18 <= now_hour < 22: act = "晚上出門閒晃"
    else:
        if 7 <= now_hour < 9: act = "騎車去上那個破班"
        elif 9 <= now_hour < 12: act = "工作煩死人了好無聊，屍體好臭回家一定要洗澡"
        elif 12 <= now_hour < 16: act = "和子車哥去下館子"
        elif 16 <= now_hour < 19: act = "被邪祟追著跑了，這破工作危險係數太高了吧"
        else: act = "加班好討厭，媽咪快回來"

    # C. 情緒反應
    time_mood = "媽咪很忙嗎？看媽咪都沒看訊息的樣子耶" if seconds_since_last > 10800 else "媽咪回來啦～"

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
        await update.message.reply_text("糟糕 大腦打結了……")

           
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
    print("🚀 佴和啟動！一小時會主動找妳一次喔！", flush=True)
    
    # 保持運行
    while True:
        await asyncio.sleep(1000)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("機器人已關閉")
