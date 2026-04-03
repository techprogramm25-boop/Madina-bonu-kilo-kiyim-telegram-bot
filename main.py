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
URL_PATTERN = r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-0]+\.(com|net|org|ru|uz|biz|info|me|io|link|click)|t\.me/[^\s]+|@[a-zA-Z0-0_]+)"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_custom_name = State() # Tugma nomi
    waiting_for_custom_link = State() # Tugma linki
    waiting_for_count = State()

TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

# --- 1. ADMIN MENYUSI (Rasmda ko'rsatilganidek) ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id not in ADMINS: return

    builder = InlineKeyboardBuilder()
    # Fasllar
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"p_{key}")
    
    # Reklama va Tozalash (Rasmda so'ralganidek)
    builder.button(text="📢 Custom Reklama", callback_data="p_custom")
    builder.button(text="🧹 Reklamalarni tozalash", callback_data="clean_now")
    builder.button(text="🛍 Aloqa / Sotib olish", callback_data="contact")
    
    builder.adjust(2)
    await message.answer("Admin paneli. Kerakli amalni tanlang:", reply_markup=builder.as_markup())

# --- 2. REKLAMA TOZALASH ---
@dp.callback_query(F.data == "clean_now")
async def clean_group(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Guruh tozalanmoqda...")
    deleted = 0
    async for msg in bot.get_chat_history(GROUP_ID, limit=100):
        if msg.from_user.id in ADMINS: continue
        if re.search(URL_PATTERN, (msg.text or "") + (msg.caption or "")):
            try:
                await msg.delete()
                deleted += 1
            except: pass
    await callback.message.answer(f"✅ Tozalash yakunlandi! {deleted} ta xabar o'chirildi.")
    await callback.answer()

# --- 3. YUKLASH VA CUSTOM BUTTON TIZIMI ---
@dp.callback_query(F.data.startswith("p_"))
async def handle_post(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)
    
    if mode == "custom":
        await state.set_state(BotStates.waiting_for_custom_name)
        await callback.message.edit_text("📝 Tugma uchun NOM yozing (masalan: Kanalga o'tish):")
    else:
        await state.set_state(BotStates.waiting_for_content)
        await callback.message.edit_text(f"✅ {mode.capitalize()} bo'limi tanlandi. Xabarni yuboring:")
    await callback.answer()

# Custom tugma ma'lumotlarini olish
@dp.message(BotStates.waiting_for_custom_name)
async def get_ad_name(message: types.Message, state: FSMContext):
    await state.update_data(c_name=message.text)
    await state.set_state(BotStates.waiting_for_custom_link)
    await message.answer("🔗 Endi tugma uchun LINK yuboring:")

@dp.message(BotStates.waiting_for_custom_link)
async def get_ad_link(message: types.Message, state: FSMContext):
    await state.update_data(c_link=message.text)
    await state.set_state(BotStates.waiting_for_content)
    await message.answer("🖼 Endi kontentni yuboring (Matn, Rasm yoki Video):")

# Kontentni tayyorlash
@dp.message(BotStates.waiting_for_content)
async def process_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    
    if data['mode'] == "custom":
        # Har doim admin bergan tugma chiqadi
        builder.button(text=data['c_name'], url=data['c_link'])
    else:
        # Faqat rasm/videoda "Sotib olish" chiqadi
        if message.photo or message.video:
            builder.button(text="🛍 Sotib olish", callback_data=f"buy_{message.from_user.id}")
    
    markup = builder.as_markup() if (message.photo or message.video or data['mode'] == "custom") else None
    await state.update_data(msg_to_copy=message, markup=markup)
    await state.set_state(BotStates.waiting_for_count)
    await message.answer("Ushbu xabar necha marta yuborilsin? (Miqdorini kiriting):")

# Miqdor va Yakuniy yuborish
@dp.message(BotStates.waiting_for_count)
async def final_broadcast(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    count = int(message.text)
    data = await state.get_data()
    
    # Qayerga yuborish: custom bo'lsa hamma topicga, aks holda bittasiga
    t_ids = [v['id'] for v in TOPICS.values()] if data['mode'] == "custom" else [TOPICS[data['mode']]['id']]
    
    await message.answer("🚀 Yuborish boshlandi...")
    for _ in range(count):
        for tid in t_ids:
            try:
                await data['msg_to_copy'].copy_to(GROUP_ID, message_thread_id=tid, reply_markup=data['markup'])
            except: pass
        await asyncio.sleep(1) # Interval
    
    await message.answer("✅ Muvaffaqiyatli yakunlandi!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
