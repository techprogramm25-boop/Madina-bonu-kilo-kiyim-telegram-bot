import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
GROUP_ID = -1002380596336 

# Sening Topic ID-laring
TOPICS = {
    "bahor": {"id": 4, "name": "🌸 Bahorgi kiyimlar"},
    "yoz": {"id": 6, "name": "🌞 Yozgi kiyimlar"},
    "kuz": {"id": 8, "name": "🍂 Kuzgi kiyimlar"},
    "qish": {"id": 2, "name": "❄️ Qishki kiyimlar"}
}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class UploadState(StatesGroup):
    uploading = State()

# --- START ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=v["name"], callback_data=f"up_{k}")] for k, v in TOPICS.items()
    ])
    await message.answer("Qaysi bo'limga kiyim yuklaymiz?", reply_markup=kb)

# --- BO'LIMNI TANLASH ---
@dp.callback_query(F.data.startswith("up_"))
async def select_topic(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.split("_")[1]
    await state.update_data(topic_key=key)
    await state.set_state(UploadState.uploading)
    await callback.message.edit_text(
        f"✅ {TOPICS[key]['name']} tanlandi.\n\n"
        "Endi Rasm, GIF, Video yoki Tekst yuboring. Men uni guruhga tashlayman!\n"
        "To'xtatish uchun /stop deb yozing."
    )

# --- STOP ---
@dp.message(Command("stop"))
async def stop_upload(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bo'limdan chiqdingiz. Yangidan tanlash uchun /start bosing.")

# --- HAMMA NARSANI TANIDIGAN FUNKSIYA ---
@dp.message(UploadState.uploading)
async def handle_universal_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    topic_key = data.get("topic_key")
    thread_id = TOPICS[topic_key]['id']
    
    try:
        # copy_to - bu hamma narsani (image, gif, video, audio, text) 
        # avtomatik taniydi va bot nomidan guruhga nusxalaydi.
        await message.copy_to(
            chat_id=GROUP_ID,
            message_thread_id=thread_id
        )
        # Foydalanuvchiga tasdiqlash xabari (xohlasang buni o'chirib qo'yish mumkin)
        await message.reply("✅ Tashlandi!")
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}\n\nEslatma: Bot guruhda ADMIN bo'lishi va 'Manage Topics' huquqi yoqilgan bo'lishi shart!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
