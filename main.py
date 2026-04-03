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
GROUP_ID = -1002380596336 
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
        "Salom! Qaysi fasl bo'limiga kiyim yuklamoqchisiz?\nTanlang va keyin xohlagan faylingizni yuboring.",
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
        "Endi Rasm, Video, GIF yoki Tekst yuboring.\n"
        "Boshqa bo'limga o'tish uchun /stop deb yozing."
    )

# --- STOP ---
@dp.message(Command("stop"))
async def stop_upload(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bo'limdan chiqdingiz. Yangidan tanlash uchun /start bosing.")

# --- UNIVERSAL YUBORISH (Hamma fayl turi uchun) ---
@dp.message(UploadState.uploading)
async def handle_upload(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    now = time.time()
    
    # 4 soniya kutish (Antispam)
    if user_id in last_msg_time and now - last_msg_time[user_id] < 4:
        wait = 4 - int(now - last_msg_time[user_id])
        return await message.answer(f"Iltimos, {wait} soniya kuting...")
    
    last_msg_time[user_id] = now
    data = await state.get_data()
    topic_key = data.get("current_topic")
    thread_id = TOPICS[topic_key]["id"]

    try:
        # COPY_TO - Bu eng yaxshi usul, hamma narsani (GIF, Video, Audio) 
        # bot nomidan original holatda yuboradi.
        await message.copy_to(
            chat_id=GROUP_ID,
            message_thread_id=thread_id
        )
        await message.answer("✅ Muvaffaqiyatli yuborildi!")
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}\n\nEslatma: Bot guruhda ADMIN bo'lishi va 'Manage Topics' huquqi yoqilgan bo'lishi shart!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
