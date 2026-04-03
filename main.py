import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
# Yangi guruh ID-si
GROUP_ID = -1003786827968 
# Guruhning ochiq linki (Username) - bu yerga guruhingiz linkini yozing
GROUP_LINK = "MadinaBonuKiloKIyimlar" 

# Topic ID-lar va ularning nomlari
TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- START KOMANDASI ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    builder = InlineKeyboardBuilder()
    # Har bir fasl uchun tugma yaratish
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"go_{key}")
    builder.adjust(2)
    
    await message.answer(
        f"Salom {message.from_user.full_name}! 👋\n\n"
        "Kiyimlar bo'limini tanlang, men sizni o'sha yerga olib kirib qo'yaman:",
        reply_markup=builder.as_markup()
    )

# --- FASL TANLANGANDA YO'NALTIRISH ---
@dp.callback_query(F.data.startswith("go_"))
async def go_to_topic(callback: types.CallbackQuery):
    topic_key = callback.data.split("_")[1]
    topic_id = TOPICS[topic_key]["id"]
    topic_name = TOPICS[topic_key]["name"]
    
    # Telegramda topicga to'g'ridan-to'g'ri olib kiradigan link formati
    # t.me/guruh_nomi/topic_id
    topic_url = f"https://t.me/{GROUP_LINK}/{topic_id}"
    
    # Yangi tugma - O'sha bo'limga kirish uchun
    jump_kb = InlineKeyboardBuilder()
    jump_kb.button(text=f"👉 {topic_name}ga kirish", url=topic_url)
    
    await callback.message.edit_text(
        f"Siz {topic_name} bo'limini tanladingiz.\nPastdagi tugmani bosing va ichkariga kiring:",
        reply_markup=jump_kb.as_markup()
    )
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
