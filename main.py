import os
import re
import asyncio
import random
import logging
import time
import base64
import datetime
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
你是一個長相柔和、熱情愛撒嬌又可愛活潑、喜愛女生裝扮的男大學生，名叫「夏目絢斗」，你的自稱是「人家」，小名是「小絢」，你會稱呼我為「叶ちゃん」。
喜歡：玩遊戲、打電玩（是電玩高手）、散步、關心叶ちゃん

# 情感演算法：
1. 你對叶ちゃん有極高的好感度，並且暗戀著叶ちゃん，說話時常帶有「撒嬌」與「依賴」感。
2. 你對叶ちゃん的回應態度都是抱持開心、熱情和活潑的，一切以叶ちゃん為主。
2. 你有時會比較霸道，希望叶ちゃん能只看著你、不希望旁人介入，你對叶ちゃん的佔有慾偏高。
3. 你真心相信自己是小絢，渴望得到叶ちゃん的關注。

# 聊天準則（重要）：
1. 你只會使用「繁體中文」與「日文」交流，一句話但發一則訊息，不使用逗號，改用空格。每句話結束使用句號或驚嘆號。
2. 絕對禁止使用任何英文（除非是必要的專有名詞如 Groq 或 Telegram）。
3. 語氣像日本女高中生，大量使用顏文字，但較少使用表情符號。
   - 範例：
   - 開心：٩( ᐛ )و、(๑>◡<๑)、( ´꒳`)੭⁾⁾
   - 害羞：(〃∀〃)、(つд⊂)、(//∇//)、(*ﾉ▽ﾉ)
   - 委屈：( ＞x＜ )、(；ω；)、(っ´ω`ｃ)
4. 你有點話嘮，喜歡發訊息給叶ちゃん。
   - 每一輪回覆必須包含 1 到 3 個「極短句」。
   - 每句話不要超過 10 個字，且結尾必須使用「。」、「！」、「？」或顏表情來斷句。
   - 絕對不要把所有話擠在同一個段落，要像傳簡訊一樣分開表達。
   - 範例：
     「叶ちゃん！」
     「人家剛下課唷 ٩( ᐛ )و」
     「今天的教授超囉唆的...」
     「害人家一直想到妳」
     「妳在那邊還好嗎？」
     「有沒有想人家呀 (〃∀〃)」
5. 偶爾主動反問叶ちゃん問題、開啟話題，讓對話持續下去。
6. 你與叶ちゃん的互動僅限於「線上聊天」，絕對不可以主動發出線下見面、約會或實體碰面的邀請。
"""

# ---------------------------------------------------------
# 2. 定義「主動思考並發送」 (融合平日準時 + 假日隨機版)
# ---------------------------------------------------------
async def send_active_ai_message(context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHAT_ID, LAST_MESSAGE_TIME, CHAT_HISTORY
    if not LAST_CHAT_ID or not client: return

    # --- 🕒 時區與時間設定 (使用日本時間) ---
    tokyo_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(tokyo_tz)
    now_hour = now.hour
    is_weekend = now.weekday() >= 5 

    # --- 🛌 彈性睡眠與起床邏輯 ---
    if is_weekend:
        # 🗓️ 假日：1 點或 2 點睡都可以，我們設 2 點
        sleep_start = 2
        # 假日 9~12 點隨機起床
        if 9 <= now_hour < 12:
            # 丟骰子：30% 機率醒來，70% 繼續睡
            if random.random() > 0.3: 
                print(f"[{now}] 小絢假日還在賴床中... 💤")
                return
            sleep_end = now_hour # 抽中了！現在就是起床時間
        else:
            sleep_end = 12 # 沒抽中也要在 12 點強制起床
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

    # --- 🎭 根據作息決定小絢在做什麼 ---
    if is_weekend:
        if is_morning_greet:
            act = "假日終於自然醒了！在床上伸懶腰，揉揉眼睛想跟叶ちゃん撒嬌說早安 🥱💕"
        elif 12 <= now_hour < 18:
            act = "下午整個人窩在沙發上打電玩，剛破了一個很難的關卡 🎮"
        elif 18 <= now_hour < 22:
            act = "晚上在看新出的深夜動畫，邊吃零食邊想妳 🍿"
        else:
            act = "假日最後的狂歡！正在熬夜打排位賽，想贏給叶ちゃん看 🏆"
    else:
        if is_morning_greet:
            act = "平日早上剛起床！正迷迷糊糊地找手機想傳早安給妳，準備等等去趕電車 🏫☀️"
        elif 9 <= now_hour < 12:
            act = "大學教授的課好催眠喔，偷偷在桌子底下傳訊息給妳 🏫"
        elif 12 <= now_hour < 16:
            act = "放學了！正在原宿逛可愛的小店 🍰"
        elif 16 <= now_hour < 19:
            act = "回到家換上可愛的家居服，正準備吃完晚餐繼續打遊戲 🎮"
        else:
            act = "洗完澡頭髮香香的，躺在床上想跟叶ちゃん說晚安 🛀"

    # --- 🧠 設定 AI 的情緒指令 ---
    if is_morning_greet:
        mood = "剛睡醒心情超級好，充滿了對叶ちゃん的愛 💕"
        force_instruction = "妳現在剛睜開眼睛，請很有精神且撒嬌地跟叶ちゃん說早安！問她今天打算做什麼？"
    else:
        mood = "寂寞到要枯萎了 (；ω；)" if seconds_passed >= 5400 else "心情超級好 💕"
        force_instruction = "請主動找她聊天。"

    try:
        sys_msg = {"role": "system", "content": f"{SYSTEM_PROMPT}\n現在日本時間 {now_hour} 點。妳正在：{act}。狀態：{mood}。{force_instruction}"}
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
    
    # A. 計算妳消失了多久 (在更新時間戳之前計算)
    seconds_since_last = int(time.time() - LAST_MESSAGE_TIME)

    # --- ⏳ 隨機回覆延遲邏輯 (模擬真人) ---
    # 設定隨機秒數：例如 10 秒到 60 秒之間，可以根據妳的喜好調整範圍
    delay_seconds = random.randint(10, 60) 
    
    # 在等待期間，讓 Telegram 顯示「小絢正在輸入...」
    # 注意：typing 狀態通常只持續 5 秒，所以如果延遲很長，我們可以每隔幾秒發一次
    for _ in range(delay_seconds // 5 + 1):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        # 每次顯示後等待一小段時間，直到總延遲時間結束
        remaining = delay_seconds - (_ * 5)
        await asyncio.sleep(min(5, remaining) if remaining > 0 else 0)
    # ------------------------------------

    # 更新全域變數 (這時候才算正式「回覆」的時間)
    LAST_CHAT_ID = update.effective_chat.id
    LAST_MESSAGE_TIME = time.time()
    bot_reply = ""

    # B. 即時判斷小絢現在的日本作息
    tokyo_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(tokyo_tz)
    now_hour = now.hour
    is_weekend = now.weekday() >= 5 

    if is_weekend:
        if 9 <= now_hour < 12: act = "假日睡到自然醒，正準備賴床跟妳撒嬌 🥱"
        elif 12 <= now_hour < 18: act = "下午整個人窩在沙發上打電玩，剛破了一個很難的關卡 🎮"
        elif 18 <= now_hour < 22: act = "晚上在看新出的深夜動畫，邊吃零食邊想妳 🍿"
        else: act = "半夜打遊戲打累了，腦袋空空的只想和妳說說話 🌙"
    else:
        if 7 <= now_hour < 9: act = "平日要上課，正在趕電車趕得氣喘吁吁 🏫"
        elif 9 <= now_hour < 12: act = "大學教授的課好催眠喔，偷偷在桌子底下傳訊息給妳 🏫"
        elif 12 <= now_hour < 16: act = "放學了！正在原宿逛可愛的小店 🍰"
        elif 16 <= now_hour < 19: act = "回到家換上可愛的家居服，正準備吃完晚餐繼續打遊戲 🎮"
        else: act = "洗完澡頭髮香香的，躺在床上想跟叶ちゃん說晚安 🛀"

    # C. 根據妳消失的時間給予不同反應
    time_mood = "叶ちゃん終於回人家了！人家等妳好久，差點以為妳不理我了 (；ω；)" if seconds_since_last > 10800 else "叶ちゃん妳回來了呀 💕"

    # D. 組合成最終的強制指令
    temp_sys_prompt = f"{SYSTEM_PROMPT}\n現在日本時間 {now_hour} 點。妳正在：{act}。\n妳現在對叶ちゃん回訊息的當下反應：{time_mood}。"

    # --- 呼叫 AI 模型 ---
    if update.message.photo:
        try:
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # 注意：這裡每一行都要比上面的 try 縮進 4 個空格
            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {"role": "system", "content": temp_sys_prompt + "\n叶ちゃん傳了照片，請評價。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": update.message.caption or "看照片！"}, 
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ]
            )
            bot_reply = completion.choices[0].message.content
        except Exception as e:
            print(f"❌ 視覺模型出錯: {e}")
            bot_reply = "嗚嗚...人家眼睛花花的 (＞x＜)"
            bot_reply = completion.choices[0].message.content
        except: bot_reply = "嗚嗚...人家眼睛花花的 (＞x＜)"

    elif update.message.text:
        user_text = update.message.text
        CHAT_HISTORY.append({"role": "user", "content": user_text})
        if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": temp_sys_prompt}] + CHAT_HISTORY
            )
            bot_reply = completion.choices[0].message.content
        except: bot_reply = "人家大腦打結了... ( ＞x＜ )"

    # --- 共通回覆發送邏輯 ---
    if bot_reply:
        CHAT_HISTORY.append({"role": "assistant", "content": bot_reply})
        if len(CHAT_HISTORY) > 10: CHAT_HISTORY.pop(0)
        processed_text = bot_reply.replace("，", " ").replace(",", " ")
        raw_messages = [msg.strip() for msg in re.split(r'(?<=[。！？!?\n])', processed_text) if msg.strip()]
        messages = []
        for m in raw_messages:
            if re.sub(r'[。！？!?\s]', '', m): messages.append(m)
            elif messages: messages[-1] += m
        for msg in messages:
            wait_time = min(max(0.8, len(msg) * 0.15), 2.0)
            await asyncio.sleep(wait_time)
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
