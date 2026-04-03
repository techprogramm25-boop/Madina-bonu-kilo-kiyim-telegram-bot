import asyncio
import logging
import datetime
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
GROUP_ID = -1003786827968 
ADMINS = [6977836294, 7724018139]

# Moderatsiya filtri
URL_PATTERN = r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-0]+\.(com|net|org|ru|uz|biz|info|me|io|link|click)|t\.me/[^\s]+|@[a-zA-Z0-0_]+)"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_ad_name = State()
    waiting_for_ad_link = State()
    waiting_for_count = State()
    waiting_for_reply = State()

TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahor"},
    "yoz": {"id": 6, "name": "🌞 Yoz"},
    "kuz": {"id": 8, "name": "🍂 Kuz"},
    "qish": {"id": 2, "name": "❄️ Qish"}
}

# --- 1. START VA 3 XIL ASOSIY TUGMA ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id not in ADMINS:
        return await message.answer("Siz admin emassiz!")

    builder = InlineKeyboardBuilder()
    # 1-TUGMA: Bo'limlarga yuklash
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"post_{key}")
    
    # 2-TUGMA: Custom Reklama
    builder.button(text="📢 Reklama (Custom Link)", callback_data="post_ad")
    
    # 3-TUGMA: Tozalash
    builder.button(text="🧹 Guruhni tozalash", callback_data="clean_now")
    
    builder.adjust(2)
    await message.answer("Admin paneli. Kerakli amalni tanlang:", reply_markup=builder.as_markup())

# --- 2. REKLAMA TOZALASH (Haqiqiy tozalash) ---
@dp.callback_query(F.data == "clean_now")
async def clean_group(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Reklamalar o'chirilmoqda...")
    deleted = 0
    async for msg in bot.get_chat_history(GROUP_ID, limit=100):
        if msg.from_user.id in ADMINS: continue
        content = (msg.text or "") + (msg.caption or "")
        if re.search(URL_PATTERN, content):
            try:
                await msg.delete()
                deleted += 1
            except: pass
    await callback.message.answer(f"✅ Tozalash yakunlandi! {deleted} ta reklama o'chirildi.")
    await callback.answer()

# --- 3. YUKLASH MANTIQI ---
@dp.callback_query(F.data.startswith("post_"))
async def handle_post(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.split("_")[1]
    await state.update_data(mode=key)
    
    if key == "ad":
        await state.set_state(BotStates.waiting_for_ad_name)
        await callback.message.edit_text("📝 Reklama tugmasi uchun NOM yozing:")
    else:
        await state.set_state(BotStates.waiting_for_content)
        await callback.message.edit_text(f"✅ {key.capitalize()} bo'limi. Matn, rasm yoki video yuboring:")
    await callback.answer()

# CUSTOM REKLAMA: NOMI VA LINKI
@dp.message(BotStates.waiting_for_ad_name)
async def ad_name(message: types.Message, state: FSMContext):
    await state.update_data(ad_name=message.text)
    await state.set_state(BotStates.waiting_for_ad_link)
    await message.answer("🔗 Endi tugma uchun LINK yuboring:")

@dp.message(BotStates.waiting_for_ad_link)
async def ad_link(message: types.Message, state: FSMContext):
    await state.update_data(ad_link=message.text)
    await state.set_state(BotStates.waiting_for_content)
    await message.answer("🖼 Endi reklama kontentini (Rasm/Video/Matn) yuboring:")

# KONTENT QABUL QILISH
@dp.message(BotStates.waiting_for_content)
async def get_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    
    if data['mode'] == "ad":
        # REKLAMA REJIMI: Har doim custom tugma qo'shiladi
        builder.button(text=data['ad_name'], url=data['ad_link'])
    else:
        # ODDIY REJIM: Faqat rasm/videoda "Sotib olish" chiqadi
        if message.photo or message.video:
            builder.button(text="🛍 Sotib olish", callback_data=f"buy_{message.from_user.id}")
    
    markup = builder.as_markup() if (message.photo or message.video or data['mode'] == "ad") else None
    await state.update_data(msg_to_copy=message, markup=markup)
    await state.set_state(BotStates.waiting_for_count)
    await message.answer("Necha marta yuborilsin?")

@dp.message(BotStates.waiting_for_count)
async def final_step(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    count = int(message.text)
    data = await state.get_data()
    
    # Qayerga yuborish
    t_ids = [v['id'] for v in TOPICS.values()] if data['mode'] == "ad" else [TOPICS[data['mode']]['id']]
    
    for _ in range(count):
        for tid in t_ids:
            try:
                await data['msg_to_copy'].copy_to(GROUP_ID, message_thread_id=tid, reply_markup=data['markup'])
            except: pass
        await asyncio.sleep(2)
    
    await message.answer("✅ Tayyor!")
    await state.clear()

# --- ALOQA TIZIMI ---
@dp.callback_query(F.data.startswith("buy_"))
async def buy_req(callback: types.CallbackQuery):
    for adm in ADMINS:
        try:
            kb = InlineKeyboardBuilder().button(text="Javob berish", callback_data=f"rep_{callback.from_user.id}")
            await bot.send_message(adm, f"🛒 So'rov: {callback.from_user.full_name}", reply_markup=kb.as_markup())
        except: pass
    await callback.answer("Adminga xabar ketdi!", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
