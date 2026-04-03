import asyncio
import logging
import datetime
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

# Taqiqlangan so'zlar
BAD_WORDS = ["soka", "xarom", "iflos", "skat", "qanjiq"] 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
user_violations = {}

class BotStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_count = State()
    waiting_for_reply = State()

TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

# --- 1. ANTISPAM VA ANTIREKLAMA ---
@dp.message(F.chat.id == GROUP_ID)
async def antispam_handler(message: types.Message):
    if message.from_user.id in ADMINS:
        return

    content = (message.text or "") + (message.caption or "")
    content = content.lower()
    
    is_bad = False
    if any(link in content for link in ["http", "t.me/", "www.", "@"]): is_bad = True
    if any(word in content for word in BAD_WORDS): is_bad = True

    if is_bad:
        try:
            await message.delete()
            u_id = message.from_user.id
            user_violations[u_id] = user_violations.get(u_id, 0) + 1
            
            # Jazoni hisoblash
            if user_violations[u_id] == 1:
                until = datetime.datetime.now() + datetime.timedelta(hours=1, minutes=58)
                msg = "⚠️ 1 soat 58 daqiqaga bloklandingiz!"
            else:
                until = datetime.datetime.now() + datetime.timedelta(hours=9)
                msg = "⚠️ Qoidani yana buzganingiz uchun 9 soatga bloklandingiz!"

            await bot.restrict_chat_member(
                chat_id=GROUP_ID,
                user_id=u_id,
                permissions=types.ChatPermissions(can_send_messages=False),
                until_date=until
            )
            await message.answer(f"{message.from_user.first_name}, {msg}")
        except: pass

# --- 2. START VA ADMIN MENYU ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"go_{key}")
    
    if message.from_user.id in ADMINS:
        builder.button(text="📢 Hammasiga yuborish", callback_data="go_all")
    
    builder.button(text="🛍 Sotib olish / Aloqa", callback_data="buy_contact")
    builder.adjust(2)
    await message.answer("Bo'limni tanlang:", reply_markup=builder.as_markup())

# --- 3. ADMIN JONATISh TIZIMI ---
@dp.callback_query(F.data.startswith("go_"))
async def handle_choice(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.split("_")[1]
    if callback.from_user.id in ADMINS:
        await state.update_data(topic_key=key)
        await state.set_state(BotStates.waiting_for_content)
        await callback.message.edit_text("Narsa yuboring (Rasm/Video/Matn):")
    else:
        if key == "all": return
        url = f"https://t.me/{GROUP_LINK}/{TOPICS[key]['id']}"
        kb = InlineKeyboardBuilder().button(text="➡️ Kirish", url=url)
        await callback.message.edit_text(f"{TOPICS[key]['name']}ga o'tish:", reply_markup=kb.as_markup())

@dp.message(BotStates.waiting_for_content)
async def get_content(message: types.Message, state: FSMContext):
    await state.update_data(msg_to_copy=message)
    await state.set_state(BotStates.waiting_for_count)
    await message.answer("Necha marta yuborilsin?")

@dp.message(BotStates.waiting_for_count)
async def finish_upload(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    count = min(int(message.text), 50)
    data = await state.get_data()
    t_key = data['topic_key']
    t_ids = [v['id'] for v in TOPICS.values()] if t_key == "all" else [TOPICS[t_key]['id']]

    for _ in range(count):
        for tid in t_ids:
            try: await data['msg_to_copy'].copy_to(GROUP_ID, message_thread_id=tid)
            except: pass
        await asyncio.sleep(2)
    await message.answer("✅ Tayyor!")
    await state.clear()

# --- 4. ALOQA TIZIMI ---
@dp.callback_query(F.data == "buy_contact")
async def buy_req(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder().button(text="Javob berish 💬", callback_data=f"reply_{callback.from_user.id}")
    for adm in ADMINS:
        try: await bot.send_message(adm, f"🛍 So'rov!\nIsm: {callback.from_user.full_name}\nID: {callback.from_user.id}", reply_markup=kb.as_markup())
        except: pass
    await callback.message.answer("Adminga xabar ketdi!")

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
