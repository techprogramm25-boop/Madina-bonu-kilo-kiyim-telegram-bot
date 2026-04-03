import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = '8684928003:AAHdpSFmNwijOijqQCwblUGbcikoPUxiZGo'
# Guruh ssilkasi orqali aniqlangan ID
GROUP_ID = -1002380596336 

# Topic ID-lar (Ssilkadagi oxirgi raqamlar)
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
    builder = InlineKeyboardBuilder()
    for key, val in TOPICS.items():
        builder.button(text=val["name"], callback_data=f"up_{key}")
    builder.adjust(2)
    await message.answer("Qaysi bo'limga yuklaymiz?", reply_markup=builder.as_markup())

# --- TOPIC TANLASH ---
@dp.callback_query(F.data.startswith("up_"))
async def select_topic(callback: types.CallbackQuery, state: FSMContext):
    topic_key = callback.data.split("_")[1]
    await state.update_data(current_topic=topic_key)
    await state.set_state(UploadState.uploading)
    await callback.message.edit_text(f"✅ {TOPICS[topic_key]['name']} tanlandi. Endi rasm/video yuboring!")

# --- STOP ---
@dp.message(Command("stop"))
async def stop_upload(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("To'xtatildi. /start")

# --- YUBORISH ---
@dp.message(UploadState.uploading)
async def handle_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    topic_key = data.get("current_topic")
    thread_id = TOPICS[topic_key]["id"]

    try:
        # Eng ishonchli usul: copy_to
        await message.copy_to(
            chat_id=GROUP_ID,
            message_thread_id=thread_id
        )
        await message.answer("✅ Guruhga tashlandi!")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
