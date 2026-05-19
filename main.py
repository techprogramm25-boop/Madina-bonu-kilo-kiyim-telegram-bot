import logging
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- SOZLAMALAR ---
BOT_TOKEN = "8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo"
ADMINS = [6977836294, 8409259397]

# Guruh ID-lari
ESKI_GURUH_ID = -1001456164408  # @MADINAKILOKIYIMLAR
YANGI_GURUH_ID = -1002047814831  # Yangi super guruh ID-si

# --- TOPIC ID-LAR ---
TOPIC_XABAR_YOZISH = 1
TOPIC_QISHKI = 2
TOPIC_BAHORGI = 4
TOPIC_YOZGI = 6
TOPIC_KUZGI = 8
TOPIC_BARCHA_JAMY = 130
TOPIC_FORWARDI_ESKI = 137  # Eski guruhdan keladigan narsalar uchun

# Git-da bor bo'lgan start rasmi havolasi
START_IMAGE_URL = "https://raw.githubusercontent.com/Yusufxonpro/MadiWay/main/kilo_kiyim_madi.png" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_verification_codes = {}
verified_users = set()

# --- ADMIN PANEL TUGMALARI (aiogram 2 uslubida) ---
def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="🌸 Bahorgi kiyimlar", callback_data="admin_cat_4"),
        InlineKeyboardButton(text="☀️ Yozgi kiyimlar", callback_data="admin_cat_6"),
        InlineKeyboardButton(text="🍂 Kuzgi kiyimlar", callback_data="admin_cat_8"),
        InlineKeyboardButton(text="❄️ Qishki kiyimlar", callback_data="admin_cat_2"),
        InlineKeyboardButton(text="👗 Barcha kiyimlar", callback_data="admin_cat_130"),
        InlineKeyboardButton(text="📢 Custom Reklama", callback_data="ad_custom"),
        InlineKeyboardButton(text="🧹 Tozalash", callback_data="clear_data"),
        InlineKeyboardButton(text="🛍️ Aloqa", callback_data="contact_info"),
        InlineKeyboardButton(text="📊 Statistika", callback_data="statistika"),
        InlineKeyboardButton(text="📢 Hammasiga birda", callback_data="ad_all")
    )
    return keyboard

# --- MIJOZ PANEL TUGMALARI (aiogram 2 uslubida) ---
def get_user_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton(text="🌸 Bahorgi kiyimlar"), KeyboardButton(text="☀️ Yozgi kiyimlar"),
        KeyboardButton(text="🍂 Kuzgi kiyimlar"), KeyboardButton(text="❄️ Qishki kiyimlar"),
        KeyboardButton(text="👗 Barcha kiyimlar jami"), KeyboardButton(text="🛍️ Biz bilan aloqa")
    )
    return keyboard

# --- START BUYRUG'I ---
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    if message.from_user.id in ADMINS:
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=START_IMAGE_URL,
            caption="👋 Assalomu alaykum Admin!\n\nAdmin paneli (Jami 10 ta tugma):",
            reply_markup=get_admin_keyboard()
        )
    else:
        welcome_text = (
            "✨ **Madina Bonu Kilo Kiyimlar botiga xush kelibsiz!**\n\n"
            "Bozordagidan ancha arzon va sifatli Yevropa kiyimlari!\n"
            "O'zingizga kerakli fasl tugmasini bosing 👇"
        )
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=START_IMAGE_URL,
            caption=welcome_text,
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )

# --- MIJOZ FASL TUGMALARI ---
@dp.message_handler(lambda message: message.text in ["🌸 Bahorgi kiyimlar", "☀️ Yozgi kiyimlar", "🍂 Kuzgi kiyimlar", "❄️ Qishki kiyimlar", "👗 Barcha kiyimlar jami"])
async def show_topic_link(message: types.Message):
    links = {
        "🌸 Bahorgi kiyimlar": (TOPIC_BAHORGI, "Bahorgi kiyimlar bo'limiga o'tish"),
        "☀️ Yozgi kiyimlar": (TOPIC_YOZGI, "Yozgi kiyimlar bo'limiga o'tish"),
        "🍂 Kuzgi kiyimlar": (TOPIC_KUZGI, "Kuzgi kiyimlar bo'limiga o'tish"),
        "❄️ Qishki kiyimlar": (TOPIC_QISHKI, "Qishki kiyimlar bo'limiga o'tish"),
        "👗 Barcha kiyimlar jami": (TOPIC_BARCHA_JAMY, "Barcha kiyimlar jami bo'limiga o'tish")
    }
    topic_id, text_info = links[message.text]
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="👁️ Ko'rish", url=f"https://t.me/MadinaBonuKiloKIyimlar/{topic_id}"))
    
    await message.answer(f"👇 Quyidagi tugma orqali {text_info}:", reply_markup=keyboard)

# --- ESKI GURUHNI REKLAMADAN TOZALASH VA FORWARD ---
@dp.message_handler(chat_id=ESKI_GURUH_ID, content_types=types.ContentTypes.ANY)
async def eski_guruh_handler(message: types.Message):
    # 1. Antispam: Reklama linklarini tozalash
    if message.text and ("t.me/" in message.text or "http" in message.text or "@" in message.text):
        if message.from_user.id not in ADMINS:
            try:
                await message.delete()
                return
            except Exception:
                pass

    # 2. Avtomatik Forward (Yangi guruhning 137-topiciga)
    try:
        await bot.forward_message(
            chat_id=YANGI_GURUH_ID,
            from_chat_id=ESKI_GURUH_ID,
            message_id=message.message_id
            # DIQQAT: aiogram 2 da superguruh ichidagi aniq topic_id ga to'g'ridan-to'g'ri forward qilish cheklangan bo'lishi mumkin. 
            # Agar xabar umumiy guruhga tushsa, yangi guruh havolasini ishlating.
        )
    except Exception as e:
        logging.error(f"Forward xatoligi: {e}")

# --- ESKI GURUHGA ODAM QO'SHILSA YANGISIGA TAKLIF QILISH ---
@dp.message_handler(chat_id=ESKI_GURUH_ID, content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def avto_invite_handler(message: types.Message):
    for member in message.new_chat_members:
        if not member.is_bot:
            invite_text = f"🎁 @{member.username} yangi guruhimizga ham qo'shiling: https://t.me/MadinaBonuKiloKIyimlar"
            await message.answer(invite_text)

# --- YANGI GURUH ICHIDAGI VERIFIKATSIYA (KOD TIZIMI) ---
@dp.message_handler(chat_id=YANGI_GURUH_ID, content_types=types.ContentTypes.TEXT)
async def yangi_guruh_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id in ADMINS or user_id in verified_users:
        return

    if user_id in user_verification_codes and message.text == str(user_verification_codes[user_id]):
        verified_users.add(user_id)
        del user_verification_codes[user_id]
        success_msg = await message.answer(f"✅ @{message.from_user.username} muvaffaqiyatli tasdiqlandingiz!")
        await asyncio.sleep(3)
        try:
            await message.delete()
            await success_msg.delete()
        except Exception:
            pass
        return

    # Guruhda 'message_thread_id' (Topic) ni tekshirish
    topic_id = message.to_python().get('message_thread_id', 1)
    if topic_id == TOPIC_XABAR_YOZISH:
        code = random.randint(1000, 9999)
        user_verification_codes[user_id] = code
        warn_text = f"⚠️ **Diqqat @{message.from_user.username}!**\nBot kodini kiriting: `{code}`"
        warn_msg = await message.answer(warn_text, parse_mode="Markdown")
        try:
            await message.delete()
        except Exception:
            pass
        await asyncio.sleep(15)
        try:
            await warn_msg.delete()
        except Exception:
            pass

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
