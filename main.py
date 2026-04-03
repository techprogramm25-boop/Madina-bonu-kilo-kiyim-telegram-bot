import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- 1. VEB-SERVER (TEKIN HOSTINGLAR UCHUN) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot 24/7 ishlamoqda!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. BOT SOZLAMALARI ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
GROUP_ID = -1002380596336  # O'zingizning guruh ID'ingiz

# Adminlar ID ro'yxati
ADMINS = [6977836294, 7724018139] 

# Topic (Mavzu) ID'lari - Bularni guruhdagi linkdan aniqlab oling
TOPICS = {
    "bahor": {"id": 2, "name": "🦄 Bahorgi Kiyimlar"},
    "yoz": {"id": 4, "name": "☀️ Yozgi Kiyimlar"},
    "kuz": {"id": 6, "name": "🛍️ Kuzgi kiyimlar"},
    "qish": {"id": 8, "name": "🏔️ Qishki Kiyimlar"}
}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- 3. ADMINLAR UCHUN START ---
@dp.message(Command("start"), F.from_user.id.in_(ADMINS))
async def admin_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"up_{key}")
    builder.adjust(2)
    await message.answer(f"Salom @{message.from_user.username}!\nSiz adminsiz. Qaysi bo'limga kiyim yuklaymiz?", 
                         reply_markup=builder.as_markup())

# --- 4. FOYDALANUVCHILAR UCHUN START ---
@dp.message(Command("start"), ~F.from_user.id.in_(ADMINS))
async def user_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=f"Ko'rish: {val['name']}", callback_data=f"view_{key}")
    builder.adjust(1)
    await message.answer("Xush kelibsiz! Qaysi fasl kiyimlarini ko'rmoqchisiz?", 
                         reply_markup=builder.as_markup())

# --- 5. YO'NALTIRISH FUNKSIYALARI ---
@dp.callback_query(F.data.startswith("view_"))
async def view_topic(callback: types.CallbackQuery):
    topic_key = callback.data.split("_")[1]
    t_id = TOPICS[topic_key]['id']
    # Guruh linkini shakllantirish (Guruh ommaviy bo'lishi kerak)
    link = f"https://t.me/c/{str(GROUP_ID)[4:]}/{t_id}"
    await callback.message.answer(f"{TOPICS[topic_key]['name']} bo'limiga o'tish:", 
                                  reply_markup=InlineKeyboardBuilder().button(text="Kirish ➡️", url=link).as_markup())

@dp.callback_query(F.data.startswith("up_"))
async def start_upload(callback: types.CallbackQuery):
    topic_name = TOPICS[callback.data.split("_")[1]]['name']
    await callback.message.answer(f"Hozircha {topic_name} uchun rasm yoki tekst yuboring, men uni guruhga yo'naltiraman.")

# --- MAIN FUNKSIYA ---
async def main():
    keep_alive() # Veb-serverni ishga tushirish
    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
