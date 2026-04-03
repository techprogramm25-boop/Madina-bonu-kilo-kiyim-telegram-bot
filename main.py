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
GROUP_ID = -1002380596336 # Guruh ID (shunday qolsin)
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

# Antispam uchun vaqtni saqlash
last_msg_time = {}

# Bot kim qaysi bo'limni tanlaganini bilishi uchun "holatlar"
class UploadState(StatesGroup):
    choosing_topic = State()
    uploading = State()

# --- START KOMANDASI ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear() # Avvalgi holatlarni o'chirish
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"up_{key}")
    builder.adjust(2)
    
    await message.answer(
        "Salom! Qaysi bo'limga narsa yuklamoqchisiz? Tanlang va keyin rasm yoki tekst yuboring.",
        reply_markup=builder.as_markup()
    )

# --- TOPICNI TANLASH ---
@dp.callback_query(F.data.startswith("up_"))
async def select_topic(callback: types.CallbackQuery, state: FSMContext):
    topic_key = callback.data.split("_")[1]
    await state.update_data(current_topic=topic_key)
    await state.set_state(UploadState.uploading)
    
    await callback.message.edit_text(
        f"✅ Tanlandi: {TOPICS[topic_key]['name']}\n\n"
        "Endi narsa yuboring (Rasm, Video yoki Tekst).\n"
        "To'xtatish va boshqa bo'limni tanlash uchun /stop deb yozing."
    )

# --- STOP KOMANDASI (Topicdan chiqish) ---
@dp.message(Command("stop"))
async def stop_upload(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bo'limdan chiqdingiz. Yangidan tanlash uchun /start bosing.")

# --- ASOSIY YUKLASH VA 4 SONIYA CHEKLOV ---
@dp.message(UploadState.uploading)
async def handle_upload(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_time = time.time()
    
    # 4 soniyalik cheklovni tekshirish
    if user_id in last_msg_time and current_time - last_msg_time[user_id] < 4:
        wait_time = 4 - int(current_time - last_msg_time[user_id])
        return await message.answer(f"Iltimos, {wait_time} soniya kuting! Botni band qilmang.")
    
    last_msg_time[user_id] = current_time
    
    data = await state.get_data()
    topic_key = data.get("current_topic")
    thread_id = TOPICS[topic_key]["id"]

    try:
        # Xabarni guruhga kerakli bo'limga (thread_id) yuborish
        await message.copy_to(
            chat_id=GROUP_ID,
            message_thread_id=thread_id
        )
        await message.answer(f"Sent! (4 soniyadan keyin yana yubora olasiz)")
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")

async def main():
    print("Bot yoqildi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
