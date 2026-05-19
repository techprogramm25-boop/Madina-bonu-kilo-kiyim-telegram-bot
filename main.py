import logging
import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

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

# Git-da bor bo'lgan start rasmi havolasi (Sizning GitHub rasmingiz to'g'ridan-to'g'ri havolasi)
START_IMAGE_URL = "https://raw.githubusercontent.com/Yusufxonpro/MadiWay/main/kilo_kiyim_madi.png" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_verification_codes = {}
verified_users = set()

# --- ADMIN PANEL TUGMALARI ---
def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🌸 Bahorgi kiyimlar", callback_data="admin_cat_4"),
        types.InlineKeyboardButton(text="☀️ Yozgi kiyimlar", callback_data="admin_cat_6")
    )
    builder.row(
        types.InlineKeyboardButton(text="🍂 Kuzgi kiyimlar", callback_data="admin_cat_8"),
        types.InlineKeyboardButton(text="❄️ Qishki kiyimlar", callback_data="admin_cat_2")
    )
    builder.row(
        types.InlineKeyboardButton(text="👗 Barcha kiyimlar", callback_data="admin_cat_130"),
        types.InlineKeyboardButton(text="📢 Custom Reklama", callback_data="ad_custom")
    )
    builder.row(
        types.InlineKeyboardButton(text="🧹 Tozalash", callback_data="clear_data"),
        types.InlineKeyboardButton(text="🛍️ Aloqa", callback_data="contact_info")
    )
    builder.row(
        types.InlineKeyboardButton(text="📊 Statistika", callback_data="statistika"),
        types.InlineKeyboardButton(text="📢 Hammasiga birda", callback_data="ad_all")
    )
    return builder.as_markup()

# --- MIJOZ PANEL TUGMALARI ---
def get_user_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🌸 Bahorgi kiyimlar"), types.KeyboardButton(text="☀️ Yozgi kiyimlar"))
    builder.row(types.KeyboardButton(text="🍂 Kuzgi kiyimlar"), types.KeyboardButton(text="❄️ Qishki kiyimlar"))
    builder.row(types.KeyboardButton(text="👗 Barcha kiyimlar jami"), types.KeyboardButton(text="🛍️ Biz bilan aloqa"))
    return builder.as_markup(resize_keyboard=True)

# --- START BUYRUG'I (Rasm bilan keladi) ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if message.from_user.id in ADMINS:
        await message.answer_photo(
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
        await message.answer_photo(
            photo=START_IMAGE_URL,
            caption=welcome_text,
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )

# --- MIJOZ FASL TUGMALARI ---
@dp.message(F.text.in_({"🌸 Bahorgi kiyimlar", "☀️ Yozgi kiyimlar", "🍂 Kuzgi kiyimlar", "❄️ Qishki kiyimlar", "👗 Barcha kiyimlar jami"}))
async def show_topic_link(message: types.Message):
    links = {
        "🌸 Bahorgi kiyimlar": (TOPIC_BAHORGI, "Bahorgi kiyimlar bo'limiga o'tish"),
        "☀️ Yozgi kiyimlar": (TOPIC_YOZGI, "Yozgi kiyimlar bo'limiga o'tish"),
        "🍂 Kuzgi kiyimlar": (TOPIC_KUZGI, "Kuzgi kiyimlar bo'limiga o'tish"),
        "❄️ Qishki kiyimlar": (TOPIC_QISHKI, "Qishki kiyimlar bo'limiga o'tish"),
        "👗 Barcha kiyimlar jami": (TOPIC_BARCHA_JAMY, "Barcha kiyimlar jami bo'limiga o'tish")
    }
    topic_id, text_info = links[message.text]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👁️ Ko'rish", url=f"https://t.me/MadinaBonuKiloKIyimlar/{topic_id}"))
    await message.answer(f"👇 Quyidagi tugma orqali {text_info}:", reply_markup=builder.as_markup())

# --- ESKI GURUHNI REKLAMADAN TOZALASH VA MASHINA FORWARDI ---
@dp.message(F.chat.id == ESKI_GURUH_ID)
async def eski_guruh_handler(message: types.Message):
    # 1. Antispam: Reklama havolalarini aniqlash va o'chirish
    if message.text and ("t.me/" in message.text or "http" in message.text or "@" in message.text):
        if message.from_user.id not in ADMINS:
            try:
                await message.delete()
                return
            except Exception:
                pass

    # 2. Avtomatik Forward: Har qanday xabarni yangi guruhning 137-topiciga yo'naltirish
    try:
        await bot.forward_message(
            chat_id=YANGI_GURUH_ID,
            from_chat_id=ESKI_GURUH_ID,
            message_id=message.message_id,
            message_thread_id=TOPIC_FORWARDI_ESKI
        )
    except Exception as e:
        logging.error(f"Forward qilishda xatolik: {e}")

# --- ESKI GURUHGA ODAM QO'SHILSA, YANGISIGA HAM INVAIT QILISH ---
@dp.message(F.chat.id == ESKI_GURUH_ID, F.new_chat_members)
async def avto_invite_handler(message: types.Message):
    for member in message.new_chat_members:
        if not member.is_bot:
            try:
                # Maxfiyligi ruxsat bergan odamlarni yangi guruhga qo'shishga urinib ko'rish
                await bot.approve_chat_join_request(chat_id=YANGI_GURUH_ID, user_id=member.id)
                # Yoki to'g'ridan-to'g'ri qo'shish buyrug'i (agar botda to'liq huquq bo'lsa)
                await bot.add_chat_members(chat_id=YANGI_GURUH_ID, user_ids=[member.id])
            except Exception:
                # Agar foydalanuvchi nastroykasida ruxsat bermasa, bot unga taklif havolasini guruhda ko'rsatadi
                invite_text = f"🎁 @{member.username} yangi guruhimizga ham qo'shiling: https://t.me/MadinaBonuKiloKIyimlar"
                await message.answer(invite_text)

# --- YANGI GURUH ICHIDAGI VERIFIKATSIYA (KOD TIZIMI) ---
@dp.message(F.chat.id == YANGI_GURUH_ID)
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

    if message.message_thread_id == TOPIC_XABAR_YOZISH:
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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
