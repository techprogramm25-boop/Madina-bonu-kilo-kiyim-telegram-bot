import asyncio
import logging
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

TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_count = State()
    waiting_for_reply = State()

# --- START ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"go_{key}")
    
    # Yangi tugma: Hamma bo'limga yuborish (Faqat Admin uchun ko'rinadi)
    if user_id in ADMINS:
        builder.button(text="📢 Hamma bo'limga yuborish", callback_data="go_all")
    
    builder.button(text="🛍 Sotib olish / Aloqa", callback_data="buy_contact")
    builder.adjust(2)

    msg = "Xush kelibsiz! Bo'limni tanlang:"
    if user_id in ADMINS:
        msg = "Salom Admin! Bo'limni tanlang yoki hamma bo'limga reklama tashlang:"
        
    await message.answer(msg, reply_markup=builder.as_markup())

# --- TUGMALARNI BOSHQARISH ---
@dp.callback_query(F.data.startswith("go_"))
async def handle_choice(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    key = callback.data.split("_")[1]
    
    if user_id in ADMINS:
        await state.update_data(topic_key=key)
        await state.set_state(BotStates.waiting_for_content)
        
        name = "Hamma bo'limlar" if key == "all" else TOPICS[key]['name']
        await callback.message.edit_text(f"✅ {name} tanlandi.\nNarsa yuboring (Rasm/Video/Matn):")
    else:
        if key == "all": return await callback.answer("Ruxsat yo'q!", show_alert=True)
        url = f"https://t.me/{GROUP_LINK}/{TOPICS[key]['id']}"
        kb = InlineKeyboardBuilder()
        kb.button(text="➡️ Bo'limga kirish", url=url)
        await callback.message.edit_text(f"{TOPICS[key]['name']} bo'limiga o'tish:", reply_markup=kb.as_markup())
    await callback.answer()

# --- ADMIN: KONTENT QABUL QILISH ---
@dp.message(BotStates.waiting_for_content)
async def get_content(message: types.Message, state: FSMContext):
    await state.update_data(msg_to_copy=message)
    await state.set_state(BotStates.waiting_for_count)
    await message.answer("Ushbu xabar necha marta yuborilsin? (Masalan: 1)")

# --- ADMIN: YUBORISH ---
@dp.message(BotStates.waiting_for_count)
async def repeat_send(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam yozing!")
    
    count = min(int(message.text), 50)
    data = await state.get_data()
    saved_msg = data['msg_to_copy']
    topic_key = data['topic_key']
    
    await message.answer(f"🚀 Yuborish boshlandi...")
    
    # Qaysi topiclarga yuborishni aniqlaymiz
    target_ids = []
    if topic_key == "all":
        target_ids = [v['id'] for v in TOPICS.values()]
    else:
        target_ids = [TOPICS[topic_key]['id']]

    for i in range(count):
        for t_id in target_ids:
            try:
                await saved_msg.copy_to(chat_id=GROUP_ID, message_thread_id=t_id)
            except Exception as e:
                logging.error(f"Xato: {e}")
        await asyncio.sleep(2) # Oraliq vaqt
            
    await message.answer("✅ Muvaffaqiyatli tugatildi!")
    await state.clear()

# --- SOTIB OLISH VA JAVOB BERISH (O'zgarishsiz qoldi) ---
@dp.callback_query(F.data == "buy_contact")
async def buy_request(callback: types.CallbackQuery):
    user = callback.from_user
    builder = InlineKeyboardBuilder()
    builder.button(text="Javob berish 💬", callback_data=f"reply_{user.id}")
    for admin in ADMINS:
        try:
            await bot.send_message(admin, f"🛍 **Sotib olish so'rovi!**\n\nKimdan: {user.full_name}\nID: {user.id}", reply_markup=builder.as_markup())
        except: pass
    await callback.message.answer("So'rovingiz yuborildi!")
    await callback.answer()

@dp.callback_query(F.data.startswith("reply_"))
async def start_reply(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(reply_to=callback.data.split("_")[1])
    await state.set_state(BotStates.waiting_for_reply)
    await callback.message.answer("Javobingizni yozing:")
    await callback.answer()

@dp.message(BotStates.waiting_for_reply)
async def send_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        await bot.send_message(data['reply_to'], f"📩 **Admin javobi:**\n\n{message.text}")
        await message.answer("✅ Javob yuborildi!")
    except: await message.answer("❌ Xato!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
