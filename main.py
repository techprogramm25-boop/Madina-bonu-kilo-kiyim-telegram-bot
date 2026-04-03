import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
GROUP_ID = -1002380596336 # O'zingizning guruh ID'ingizni tekshiring (odatda -100 bilan boshlanadi)

# Adminlar ID ro'yxati
ADMINS = [6977836294, 7724018139] 

# Topic ID'lari (Bularni guruhdagi har bir mavzuning linkidan olish mumkin)
# Masalan: t.me/c/123/456 bo'lsa, 456 - bu Thread ID
TOPICS = {
    "bahor": {"id": 2, "name": "🦄 Bahorgi Kiyimlar"}, # ID'larni o'zingiznikiga almashtiring
    "yoz": {"id": 4, "name": "☀️ Yozgi Kiyimlar"},
    "kuz": {"id": 6, "name": "🛍️ Kuzgi kiyimlar"},
    "qish": {"id": 8, "name": "🏔️ Qishki Kiyimlar"}
}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ADMIN PANEL ---
@dp.message(Command("start"), F.from_user.id.in_(ADMINS))
async def admin_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"upload_{key}")
    builder.adjust(2)
    await message.answer("Xush kelibsiz Admin! Qaysi bo'limga kiyim yuklamoqchisiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("upload_"))
async def process_upload(callback: types.CallbackQuery):
    topic_key = callback.data.split("_")[1]
    await callback.message.answer(f"{TOPICS[topic_key]['name']} uchun rasm yoki ma'lumot yuboring. Men uni guruhga joylayman.")
    # Bu yerda holatni saqlash (FSM) kerak, lekin sodda bo'lishi uchun xabarni kutamiz

# --- FOYDALANUVCHI PANEL ---
@dp.message(Command("start"), ~F.from_user.id.in_(ADMINS))
async def user_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=f"Ko'rish: {val['name']}", callback_data=f"view_{key}")
    builder.adjust(1)
    await message.answer("Xush kelibsiz! Qaysi fasl kiyimlarini ko'rmoqchisiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("view_"))
async def view_topic(callback: types.CallbackQuery):
    topic_key = callback.data.split("_")[1]
    topic_id = TOPICS[topic_key]['id']
    # Guruh linki (Mavzuga to'g'ridan-to'g'ri o'tish)
    link = f"https://t.me/c/{str(GROUP_ID)[4:]}/{topic_id}"
    await callback.message.answer(f"{TOPICS[topic_key]['name']} bo'limiga kirish uchun bosing:", 
                                  reply_markup=InlineKeyboardBuilder().button(text="Kirish", url=link).as_markup())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
