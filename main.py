import asyncio
import logging
import datetime
import re
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
GROUP_ID = -1003786827968 
ADMINS = [6977836294, 7724018139]
DB_FILE = "users.json"
URL_PATTERN = r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-0]+\.(com|net|org|ru|uz|biz|info|me|io|link|click)|t\.me/[^\s]+|@[a-zA-Z0-0_]+)"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Foydalanuvchilar bazasi
def load_users():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(DB_FILE, "w") as f: json.dump(users, f)

class BotStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_custom_name = State()
    waiting_for_custom_link = State()
    waiting_for_count = State()
    waiting_for_customer_msg = State()
    waiting_for_admin_reply = State()

# BO'LIMLAR (Endi 5 ta bo'lim bor)
TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"},
    "jami": {"id": 130, "name": "👗 Barcha kiyimlar"} # Alohida tanlanadigan bo'ldi
}

# --- 1. START VA ADMIN PANEL ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    save_user(message.from_user.id)
    builder = InlineKeyboardBuilder()

    if message.from_user.id in ADMINS:
        # 1-5: Kiyim bo'limlari
        for key, val in TOPICS.items():
            builder.button(text=val["name"], callback_data=f"p_{key}")
        
        # 6-10: Funksiyalar
        builder.button(text="📢 Custom Reklama", callback_data="p_custom")
        builder.button(text="🧹 Tozalash", callback_data="clean_now")
        builder.button(text="🛍 Aloqa", callback_data="contact")
        builder.button(text="📊 Statistika", callback_data="stats_show")
        builder.button(text="📢 Hammasiga birda", callback_data="p_all")
        
        builder.adjust(2)
        await message.answer("Admin paneli (Jami 10 ta tugma):", reply_markup=builder.as_markup())
    else:
        # Oddiy foydalanuvchi uchun
        for key, val in TOPICS.items():
            builder.button(text=val["name"], url=f"https://t.me/MadinaBonuKiloKIyimlar/{val['id']}")
        builder.button(text="🛍 Aloqa / Sotib olish", callback_data="customer_support")
        builder.adjust(2)
        await message.answer("Xush kelibsiz! Bo'limni tanlang:", reply_markup=builder.as_markup())

# --- 2. STATISTIKA ---
@dp.callback_query(F.data == "stats_show")
async def show_stats(callback: types.CallbackQuery):
    bot_users = len(load_users())
    try: group_count = await bot.get_chat_member_count(GROUP_ID)
    except: group_count = "Noma'lum"
    await callback.message.answer(f"📊 **Statistika:**\n\n👤 Bot a'zolari: {bot_users}\n🏢 Guruh a'zolari: {group_count}")
    await callback.answer()

# --- 3. YUKLASH TIZIMI ---
@dp.callback_query(F.data.startswith("p_"))
async def handle_post(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)
    
    if mode == "custom":
        await state.set_state(BotStates.waiting_for_custom_name)
        await callback.message.edit_text("📝 Tugma NOMI:")
    else:
        await state.set_state(BotStates.waiting_for_content)
        title = "Hammasiga" if mode == "all" else TOPICS.get(mode, {}).get("name", mode)
        await callback.message.edit_text(f"✅ {title} bo'limi tanlandi. Kontentni yuboring:")
    await callback.answer()

@dp.message(BotStates.waiting_for_custom_name)
async def get_ad_name(message: types.Message, state: FSMContext):
    await state.update_data(c_name=message.text); await state.set_state(BotStates.waiting_for_custom_link)
    await message.answer("🔗 Linkni yuboring:")

@dp.message(BotStates.waiting_for_custom_link)
async def get_ad_link(message: types.Message, state: FSMContext):
    await state.update_data(c_link=message.text); await state.set_state(BotStates.waiting_for_content)
    await message.answer("🖼 Reklama xabarini yuboring:")

@dp.message(BotStates.waiting_for_content)
async def process_content(message: types.Message, state: FSMContext):
    data = await state.get_data(); builder = InlineKeyboardBuilder()
    
    if data['mode'] == "custom":
        builder.button(text=data['c_name'], url=data['c_link'])
    elif message.photo or message.video:
        builder.button(text="🛍 Sotib olish", callback_data=f"buy_{message.from_user.id}")
    
    markup = builder.as_markup() if (message.photo or message.video or data['mode'] == "custom") else None
    await state.update_data(msg_to_copy=message, markup=markup); await state.set_state(BotStates.waiting_for_count)
    await message.answer("Necha marta yuborilsin?")

@dp.message(BotStates.waiting_for_count)
async def final_send(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    count = int(message.text); data = await state.get_data()
    
    # Qayerga yuborish mantiqi
    if data['mode'] in ["all", "custom"]:
        t_ids = [v['id'] for v in TOPICS.values()]
    else:
        # Faqat tanlangan bitta bo'limga (masalan 'jami' bo'lsa 130 ga)
        t_ids = [TOPICS[data['mode']]['id']]
    
    for _ in range(count):
        for tid in t_ids:
            try: await data['msg_to_copy'].copy_to(GROUP_ID, message_thread_id=tid, reply_markup=data['markup'])
            except: pass
        await asyncio.sleep(1)
    await message.answer("✅ Muvaffaqiyatli yuborildi!"); await state.clear()

# --- 4. TOZALASH VA ALOQA ---
@dp.callback_query(F.data == "clean_now")
async def clean_group(callback: types.CallbackQuery):
    deleted = 0
    async for msg in bot.get_chat_history(GROUP_ID, limit=100):
        if msg.from_user.id in ADMINS: continue
        if re.search(URL_PATTERN, (msg.text or "") + (msg.caption or "")):
            try: await msg.delete(); deleted += 1
            except: pass
    await callback.message.answer(f"✅ {deleted} ta reklama o'chirildi."); await callback.answer()

@dp.callback_query(F.data == "customer_support")
@dp.callback_query(F.data.startswith("buy_"))
async def start_chat(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_customer_msg)
    await callback.message.answer("📝 Xabaringizni yozing:"); await callback.answer()

@dp.message(BotStates.waiting_for_customer_msg)
async def forward_to_admin(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder().button(text="💬 Javob berish", callback_data=f"rep_{message.from_user.id}")
    for adm in ADMINS:
        try: await bot.send_message(adm, f"🛒 Yangi xabar: {message.text}", reply_markup=kb.as_markup())
        except: pass
    await message.answer("✅ Yuborildi."); await state.clear()

async def main(): await dp.start_polling(bot)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); asyncio.run(main())
