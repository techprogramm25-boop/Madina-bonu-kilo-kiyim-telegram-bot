import asyncio
import logging
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
GROUP_ID = -1003786827968 
ADMINS = [6977836294, 7724018139]

# Taqiqlangan so'zlar ro'yxati (Buni o'zing to'ldirishing mumkin)
BAD_WORDS = ["soka", "xarom", "iflos", "skat", "qanjiq"] 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Foydalanuvchilarning necha marta qoida buzganini eslab qolish uchun
user_violations = {}

class BotStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_count = State()
    waiting_for_reply = State()

# --- REKLAMA VA SOKINIShNI TEKSHIRISh ---
@dp.message(F.chat.id == GROUP_ID)
async def check_messages(message: types.Message):
    # Adminlarni tekshirmaymiz
    if message.from_user.id in ADMINS:
        return

    is_bad = False
    text = message.text.lower() if message.text else ""
    caption = message.caption.lower() if message.caption else ""
    full_content = text + caption

    # 1. Linklarni tekshirish
    links = ["http", "https", "t.me/", "www.", "@"]
    if any(link in full_content for link in links):
        is_bad = True

    # 2. Sokinishlarni tekshirish
    if any(word in full_content for word in BAD_WORDS):
        is_bad = True

    if is_bad:
        try:
            # Xabarni o'chirish
            await message.delete()
            
            user_id = message.from_user.id
            user_violations[user_id] = user_violations.get(user_id, 0) + 1
            
            # Bloklash vaqti
            if user_violations[user_id] == 1:
                until = datetime.datetime.now() + datetime.timedelta(hours=1, minutes=58)
                time_str = "1 soat 58 daqiqa"
            else:
                until = datetime.datetime.now() + datetime.timedelta(hours=9)
                time_str = "9 soat"

            # Foydalanuvchini Mute qilish (yozolmaydigan qilish)
            await bot.restrict_chat_member(
                chat_id=GROUP_ID,
                user_id=user_id,
                permissions=types.ChatPermissions(can_send_messages=False),
                until_date=until
            )
            
            await message.answer(f"⚠️ {message.from_user.first_name}, qoida buzganingiz uchun {time_str}ga bloklandingiz!")
        except Exception as e:
            logging.error(f"Bloklashda xato: {e}")

# --- ADMIN FUNKSIYALARI (START, YUKLASH, ALOQA) ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"go_{key}")
    if user_id in ADMINS:
        builder.button(text="📢 Hamma bo'limga yuborish", callback_data="go_all")
    builder.button(text="🛍 Sotib olish / Aloqa", callback_data="buy_contact")
    builder.adjust(2)
    msg = "Xush kelibsiz! Bo'limni tanlang:"
    if user_id in ADMINS:
        msg = "Salom Admin! Reklama tozalash tizimi yoqildi ✅"
    await message.answer(msg, reply_markup=builder.as_markup())

# ... (Oldingi koddagi go_all, handle_choice, repeat_send, buy_request funksiyalari shu yerda davom etadi)
# Kod juda uzun bo'lib ketmasligi uchun asosiy yangi qismini tepada yozdim.
# Qolgan funksiyalar o'zgarishsiz qoladi.
