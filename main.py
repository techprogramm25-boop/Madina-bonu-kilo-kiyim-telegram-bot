import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
GROUP_ID = -1002380596336 # Sening guruh ID'ing
ADMINS = [6977836294, 7724018139]

# Sening Topic ID-laring (Ssilkadagi oxirgi raqamlar)
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
    
    await message.answer(
        "Salom! Qaysi bo'limga yuklamoqchisiz? Tanlang va kiyim rasmini yoki ma'lumotini yuboring.",
        reply_markup=builder.as_markup()
    )

# --- TOPIC TANLASH ---
@dp.callback_query(F.data.startswith("up_"))
async def select_topic(callback: types.CallbackQuery, state: FSMContext):
    topic_key = callback.data.split("_")[1]
    await state.update_data(current_topic=topic_key)
    await state.set_state(UploadState.uploading)
    
    await callback.message.edit_text(
        f"✅ {TOPICS[topic_key]['name']} tanlandi.\n\n"
        "Endi narsalarni yuboring. To'xtatish uchun /stop deb yozing."
    )

# --- STOP ---
@dp.message(Command("stop"))
async def stop_upload(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bo'limdan chiqdingiz. /start bosing.")

# --- YUBORISH (ASOSIY QISM) ---
@dp.message(UploadState.uploading)
async def handle_upload(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    now = time.time()
    
    # 4 soniya kutish
    if user_id in last_msg_time and now - last_msg_time[user_id] < 4:
        return await message.answer("Iltimos, 4 soniya kuting!")
    
    last_msg_time[user_id] = now
    data = await state.get_data()
    topic_key = data.get("current_topic")
    thread_id = TOPICS[topic_key]["id"]

    try:
        # BOT TOMONIDAN YUBORISH (Xuddi bot o'zi yozgandek)
        if message.text:
            await bot.send_message(chat_id=GROUP_ID, text=message.text, message_thread_id=thread_id)
        elif message.photo:
            await bot.send_photo(chat_id=GROUP_ID, photo=message.photo[-1].file_id, caption=message.caption, message_thread_id=thread_id)
        elif message.video:
            await bot.send_video(chat_id=GROUP_ID, video=message.video.file_id, caption=message.caption, message_thread_id=thread_id)
        elif message.document:
            await bot.send_document(chat_id=GROUP_ID, document=message.document.file_id, caption=message.caption, message_thread_id=thread_id)
        
        await message.answer("✅ Guruhga muvaffaqiyatli yuborildi!")
        
    except Exception as e:
        # Xato chiqsa shu yerda ko'rinadi
        await message.answer(f"❌ Xato: Bot guruhga yubora olmadi. Bot adminligini va Topic ID ({thread_id}) ni tekshiring.\n\nDetallar: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
