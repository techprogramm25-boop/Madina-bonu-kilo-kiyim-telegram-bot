import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
# 1. API TOKENINGNI TEKSHIR (BU TO'G'RI)
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'

# 2. GURUH ID (AGAR ISHLAMASA, BOSHIDA -100 BORLIGINI TEKSHIR)
GROUP_ID = -1002380596336 

# 3. TOPIC ID-LAR (SSILKADAGI OXIRGI RAQAMLAR)
TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
last_msg_time = {}

class UploadState(StatesGroup):
    uploading = State()

# --- START ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"up_{key}")
    builder.adjust(2)
    await message.answer("Qaysi bo'limga yuklaymiz? Tanlang:", reply_markup=builder.as_markup())

# --- TOPIC TANLASH ---
@dp.callback_query(F.data.startswith("up_"))
async def select_topic(callback: types.CallbackQuery, state: FSMContext):
    topic_key = callback.data.split("_")[1]
    await state.update_data(current_topic=topic_key)
    await state.set_state(UploadState.uploading)
    await callback.message.edit_text(f"✅ {TOPICS[topic_key]['name']} tanlandi. Endi faylni yuboring!")

# --- STOP ---
@dp.message(Command("stop"))
async def stop_upload(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("To'xtatildi. /start")

# --- ASOSIY YUBORISH ---
@dp.message(UploadState.uploading)
async def handle_upload(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    now = time.time()
    
    # 4 soniya kutish
    if user_id in last_msg_time and now - last_msg_time[user_id] < 4:
        return await message.answer("Iltimos, 4 soniya kuting!")

    data = await state.get_data()
    topic_key = data.get("current_topic")
    thread_id = TOPICS[topic_key]["id"]

    status_msg = await message.answer("⏳ Guruhga yuborilmoqda...")

    try:
        # ENG MUHIM QISM: copy_to funksiyasi
        await message.copy_to(
            chat_id=GROUP_ID,
            message_thread_id=thread_id
        )
        last_msg_time[user_id] = now
        await status_msg.edit_text("✅ Guruhga muvaffaqiyatli tashlandi!")
        
    except Exception as e:
        # Agar xato bo'lsa, xatoni o'zini yozadi
        error_text = str(e)
        if "chat not found" in error_text.lower():
            await status_msg.edit_text("❌ Xato: Bot guruhni topa olmayapti. Guruh ID xato bo'lishi mumkin.")
        elif "admin" in error_text.lower() or "forbidden" in error_text.lower():
            await status_msg.edit_text("❌ Xato: Bot guruhda ADMIN emas yoki ruxsati yo'q.")
        else:
            await status_msg.edit_text(f"❌ Xatolik yuz berdi: {error_text}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

*
