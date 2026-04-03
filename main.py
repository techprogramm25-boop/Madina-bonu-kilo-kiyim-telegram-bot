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

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_link = State() # Reklama uchun link
    waiting_for_count = State()
    waiting_for_reply = State()

TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

# --- START VA ADMIN MENYU ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    builder = InlineKeyboardBuilder()
    
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"go_{key}")
    
    if user_id in ADMINS:
        builder.button(text="📢 Reklama (Tugmali)", callback_data="go_all")
    
    builder.button(text="🛍 Aloqa", callback_data="buy_contact")
    builder.adjust(2)
    await message.answer("Bo'limni tanlang:", reply_markup=builder.as_markup())

# --- ADMIN: BO'LIM TANLASH ---
@dp.callback_query(F.data.startswith("go_"))
async def handle_choice(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.split("_")[1]
    if callback.from_user.id in ADMINS:
        await state.update_data(topic_key=key)
        if key == "all":
            await state.set_state(BotStates.waiting_for_link)
            await callback.message.edit_text("🔗 Reklama tugmasi uchun link yuboring (masalan: https://instagram.com/...):")
        else:
            await state.set_state(BotStates.waiting_for_content)
            await callback.message.edit_text(f"✅ {key.capitalize()} tanlandi. Rasm yoki video yuboring:")
    else:
        # Oddiy foydalanuvchi uchun link
        t_id = TOPICS[key]['id']
        kb = InlineKeyboardBuilder().button(text="➡️ Kirish", url=f"https://t.me/{GROUP_LINK}/{t_id}")
        await callback.message.edit_text(f"{TOPICS[key]['name']} bo'limiga o'tish:", reply_markup=kb.as_markup())
    await callback.answer()

# --- ADMIN: REKLAMA LINKINI OLISH ---
@dp.message(BotStates.waiting_for_link)
async def get_ad_link(message: types.Message, state: FSMContext):
    if not message.text.startswith("http"):
        return await message.answer("❌ Iltimos, haqiqiy link yuboring (http... bilan boshlanadigan)!")
    await state.update_data(ad_link=message.text)
    await state.set_state(BotStates.waiting_for_content)
    await message.answer("Endi reklama rasm yoki videosini yuboring:")

# --- ADMIN: KONTENT VA TUGMA YARATISH ---
@dp.message(BotStates.waiting_for_content)
async def get_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    topic_key = data['topic_key']
    
    builder = InlineKeyboardBuilder()
    
    # 1. Agar rasm yoki video bo'lsa tugma qo'shamiz
    if message.photo or message.video:
        if topic_key == "all":
            # Reklama tugmasi
            builder.button(text="🔗 Batafsil ko'rish", url=data['ad_link'])
        else:
            # Sotib olish tugmasi
            builder.button(text="🛍 Sotib olish", callback_data=f"buy_{message.from_user.id}")
    
    await state.update_data(msg_to_copy=message, reply_markup=builder.as_markup() if (message.photo or message.video) else None)
    await state.set_state(BotStates.waiting_for_count)
    await message.answer("Necha marta yuborilsin? (1-50):")

# --- ADMIN: YAKUNIY YUBORISH ---
@dp.message(BotStates.waiting_for_count)
async def finish_upload(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    count = min(int(message.text), 50)
    data = await state.get_data()
    t_key = data['topic_key']
    t_ids = [v['id'] for v in TOPICS.values()] if t_key == "all" else [TOPICS[t_key]['id']]
    
    orig_msg = data['msg_to_copy']
    markup = data['reply_markup']

    await message.answer("🚀 Jarayon boshlandi...")
    for _ in range(count):
        for tid in t_ids:
            try:
                # Nusxalashda tugmani qo'shib yuboramiz
                await orig_msg.copy_to(GROUP_ID, message_thread_id=tid, reply_markup=markup)
            except: pass
        await asyncio.sleep(2)
    
    await message.answer("✅ Muvaffaqiyatli tugatildi!")
    await state.clear()

# --- SOTIB OLISH TUGMASI BOSILGANDA ---
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy_button(callback: types.CallbackQuery):
    user = callback.from_user
    kb = InlineKeyboardBuilder().button(text="Javob berish 💬", callback_data=f"reply_{user.id}")
    
    for adm in ADMINS:
        try:
            await bot.send_message(adm, f"🛒 **Yangi xaridor!**\n\nIsm: {user.full_name}\nID: {user.id}\nUsername: @{user.username or 'yoq'}", reply_markup=kb.as_markup())
        except: pass
    
    await callback.answer("So'rovingiz adminga yuborildi! ✅", show_alert=True)

# --- ADMIN JAVOBI ---
@dp.callback_query(F.data.startswith("reply_"))
async def start_rep(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(reply_to=callback.data.split("_")[1])
    await state.set_state(BotStates.waiting_for_reply)
    await callback.message.answer("Foydalanuvchiga javobingizni yozing:")

@dp.message(BotStates.waiting_for_reply)
async def send_rep(message: types.Message, state: FSMContext):
    d = await state.get_data()
    try:
        await bot.send_message(d['reply_to'], f"📩 **Admin javobi:**\n\n{message.text}")
        await message.answer("✅ Javob foydalanuvchiga yuborildi!")
    except:
        await message.answer("❌ Yuborib bo'lmadi.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
