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
GROUP_LINK = "MadinaBonuKiloKIyimlar"
ADMINS = [6977836294, 7724018139]

# Linklar va yomon so'zlar filtri
URL_PATTERN = r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-0]+\.(com|net|org|ru|uz|biz|info|me|io|link|click)|t\.me/[^\s]+|@[a-zA-Z0-0_]+)"
BAD_WORDS = ["soka", "xarom", "iflos", "skat", "qanjiq", "jalab", "am", "itdan tarqagan", "axmoq"] 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
user_violations = {}

class BotStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_link = State()
    waiting_for_count = State()
    waiting_for_reply = State()

TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

# --- 1. AVTOMATIK TARTIB SAQLASH (Urush, Sokinish, Reklama) ---
@dp.message(F.chat.id == GROUP_ID)
async def auto_mod(message: types.Message):
    if message.from_user.id in ADMINS: return
    
    content = (message.text or "") + (message.caption or "")
    is_bad = False
    
    # Reklama yoki so'kinishni tekshirish
    if re.search(URL_PATTERN, content, re.IGNORECASE): is_bad = True
    if any(w in content.lower() for w in BAD_WORDS): is_bad = True
    
    if is_bad:
        try:
            await message.delete()
            u_id = message.from_user.id
            user_violations[u_id] = user_violations.get(u_id, 0) + 1
            
            # Jazo muddati (1:58 soat yoki 9 soat)
            duration = datetime.timedelta(hours=1, minutes=58) if user_violations[u_id] == 1 else datetime.timedelta(hours=9)
            until = datetime.datetime.now() + duration
            
            await bot.restrict_chat_member(GROUP_ID, u_id, types.ChatPermissions(can_send_messages=False), until_date=until)
            await message.answer(f"⚠️ {message.from_user.first_name} tartibni buzgani uchun bloklandi!")
        except: pass

# --- 2. START VA ADMIN PANEL ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"go_{key}")
    
    if message.from_user.id in ADMINS:
        builder.button(text="📢 Hammasiga birda yuborish", callback_data="go_all")
        builder.button(text="🧹 Reklamalarni tozalash", callback_data="clean_now")
    
    builder.button(text="🛍 Aloqa / Sotib olish", callback_data="buy_contact")
    builder.adjust(2)
    await message.answer("Assalomu alaykum! Kerakli bo'limni tanlang:", reply_markup=builder.as_markup())

# --- 3. REKLAMALARNI TOZALASH ---
@dp.callback_query(F.data == "clean_now")
async def clean_spam(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS: return
    await callback.message.answer("🔍 Guruh tozalanmoqda, kuting...")
    count = 0
    async for msg in bot.get_chat_history(GROUP_ID, limit=100):
        if msg.from_user.id in ADMINS: continue
        if re.search(URL_PATTERN, (msg.text or "") + (msg.caption or ""), re.IGNORECASE):
            try: 
                await msg.delete()
                count += 1
            except: pass
    await callback.message.answer(f"✅ Tozalash yakunlandi! {count} ta xabar o'chirildi.")
    await callback.answer()

# --- 4. YUKLASH TIZIMI ---
@dp.callback_query(F.data.startswith("go_"))
async def handle_choice(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.split("_")[1]
    if callback.from_user.id in ADMINS:
        await state.update_data(topic_key=key)
        if key == "all":
            await state.set_state(BotStates.waiting_for_link)
            await callback.message.edit_text("🔗 Reklama tugmasi uchun link yuboring (yoki 'yoq' deb yozing):")
        else:
            await state.set_state(BotStates.waiting_for_content)
            await callback.message.edit_text(f"✅ {key.capitalize()} tanlandi. Rasm/Video yuboring:")
    else:
        url = f"https://t.me/{GROUP_LINK}/{TOPICS[key]['id']}"
        await callback.message.edit_text(f"Bo'limga kirish:", reply_markup=InlineKeyboardBuilder().button(text="➡️ Kirish", url=url).as_markup())
    await callback.answer()

@dp.message(BotStates.waiting_for_link)
async def get_ad_link(message: types.Message, state: FSMContext):
    await state.update_data(ad_link=message.text)
    await state.set_state(BotStates.waiting_for_content)
    await message.answer("Endi rasm yoki videoni yuboring:")

@dp.message(BotStates.waiting_for_content)
async def get_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    if message.photo or message.video:
        if data['topic_key'] == "all" and data.get('ad_link') != "yoq":
            builder.button(text="🔗 Batafsil ko'rish", url=data['ad_link'])
        else:
            builder.button(text="🛍 Sotib olish", callback_data=f"buy_{message.from_user.id}")
    
    await state.update_data(msg_to_copy=message, markup=builder.as_markup() if (message.photo or message.video) else None)
    await state.set_state(BotStates.waiting_for_count)
    await message.answer("Necha marta yuborilsin? (1-50):")

@dp.message(BotStates.waiting_for_count)
async def finish_send(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    count = min(int(message.text), 50)
    data = await state.get_data()
    t_ids = [v['id'] for v in TOPICS.values()] if data['topic_key'] == "all" else [TOPICS[data['topic_key']]['id']]
    
    for _ in range(count):
        for tid in t_ids:
            try: await data['msg_to_copy'].copy_to(GROUP_ID, message_thread_id=tid, reply_markup=data['markup'])
            except: pass
        await asyncio.sleep(2)
    await message.answer("✅ Barcha bo'limlarga yuklandi!")
    await state.clear()

# --- 5. ALOQA ---
@dp.callback_query(F.data.startswith("buy_"))
@dp.callback_query(F.data == "buy_contact")
async def contact_admin(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder().button(text="Javob berish 💬", callback_data=f"reply_{callback.from_user.id}")
    for adm in ADMINS:
        try: await bot.send_message(adm, f"🛒 So'rov!\nIsm: {callback.from_user.full_name}\nID: {callback.from_user.id}", reply_markup=kb.as_markup())
        except: pass
    await callback.answer("Adminga xabar yuborildi!", show_alert=True)

@dp.callback_query(F.data.startswith("reply_"))
async def start_rep(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(reply_to=callback.data.split("_")[1])
    await state.set_state(BotStates.waiting_for_reply)
    await callback.message.answer("Javobingizni yozing:")

@dp.message(BotStates.waiting_for_reply)
async def send_rep(message: types.Message, state: FSMContext):
    d = await state.get_data()
    try: await bot.send_message(d['reply_to'], f"📩 Admin javobi:\n\n{message.text}")
    except: pass
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
