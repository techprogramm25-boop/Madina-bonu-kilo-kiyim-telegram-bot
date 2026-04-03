import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
GROUP_ID = -1003786827968  # Yangi guruh ID-si
GROUP_LINK = "MadinaBonuKiloKIyimlar" # Guruh username (t.me/ dan keyingi qismi)

# Adminlar ID ro'yxati (Sen va sheriging)
ADMINS = [6977836294, 7724018139]

TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class AdminState(StatesGroup):
    uploading = State()

# --- START KOMANDASI ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"choice_{key}")
    builder.adjust(2)

    if user_id in ADMINS:
        text = "Xush kelibsiz, Admin! 🛠\nQaysi bo'limga narsa yuklamoqchisiz?"
    else:
        text = f"Salom {message.from_user.first_name}! 👋\nKiyimlar bo'limini tanlang va ichkariga kiring:"
    
    await message.answer(text, reply_markup=builder.as_markup())

# --- TUGMA BOSILGANDA ---
@dp.callback_query(F.data.startswith("choice_"))
async def handle_choice(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    topic_key = callback.data.split("_")[1]
    topic_id = TOPICS[topic_key]["id"]
    topic_name = TOPICS[topic_key]["name"]

    if user_id in ADMINS:
        # ADMIN UCHUN: Yuklash rejimini yoqish
        await state.update_data(current_topic=topic_key)
        await state.set_state(AdminState.uploading)
        await callback.message.edit_text(f"✅ {topic_name} tanlandi.\nEndi rasm, video yoki tekst yuboring, men guruhga tashlayman!")
    else:
        # ODDIY FOYDALANUVCHI UCHUN: Guruhga link berish
        topic_url = f"https://t.me/{GROUP_LINK}/{topic_id}"
        jump_kb = InlineKeyboardBuilder()
        jump_kb.button(text=f"👉 {topic_name}ga kirish", url=topic_url)
        
        await callback.message.edit_text(
            f"Marhamat, {topic_name} bo'limiga o'tish uchun pastdagi tugmani bosing:",
            reply_markup=jump_kb.as_markup()
        )
    await callback.answer()

# --- ADMIN TOMONIDAN YUKLASH ---
@dp.message(AdminState.uploading)
async def admin_upload(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    data = await state.get_data()
    topic_key = data.get("current_topic")
    thread_id = TOPICS[topic_key]["id"]

    try:
        # copy_to hamma narsani (image, gif, video, text) avtomatik taniydi
        await message.copy_to(
            chat_id=GROUP_ID,
            message_thread_id=thread_id
        )
        await message.reply(f"✅ {TOPICS[topic_key]['name']} bo'limiga muvaffaqiyatli tashlandi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
