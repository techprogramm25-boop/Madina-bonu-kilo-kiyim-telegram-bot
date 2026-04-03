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
ADMINS = [6977836294, 7724018139] # Sening ID raqaming bo'lishi shart

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_repeat_text = State()
    waiting_for_repeat_count = State()
    waiting_for_admin_msg = State()
    waiting_for_reply_msg = State()

# --- START ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="🔁 Xabarni qaytarish", callback_data="menu_repeat")
    builder.button(text="✍️ Adminga yozish", callback_data="menu_admin")
    builder.adjust(1)
    
    await message.answer(f"Salom {message.from_user.first_name}! Kerakli bo'limni tanlang:", 
                         reply_markup=builder.as_markup())

# --- REPEAT (QAYTARISH) BO'LIMI ---
@dp.callback_query(F.data == "menu_repeat")
async def repeat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_repeat_text)
    await callback.message.answer("Qaytarish uchun matnni yuboring:")
    await callback.answer()

@dp.message(BotStates.waiting_for_repeat_text)
async def get_repeat_text(message: types.Message, state: FSMContext):
    await state.update_data(rep_text=message.text)
    await state.set_state(BotStates.waiting_for_repeat_count)
    await message.answer("Necha marta yuborilsin? (Maksimum 50 gacha raqam yozing):")

@dp.message(BotStates.waiting_for_repeat_count)
async def do_repeat(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqam yozing!")
    
    count = min(int(message.text), 50) # Maksimum 50 ta
    data = await state.get_data()
    text = data['rep_text']
    
    await message.answer(f"Boshladik! {count} marta yuboriladi...")
    for i in range(count):
        await message.answer(text)
        await asyncio.sleep(3) # 3 soniya interval
    
    await message.answer("✅ Tugatildi!")
    await state.clear()

# --- ADMIN BILAN ALOQA ---
@dp.callback_query(F.data == "menu_admin")
async def admin_contact(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_admin_msg)
    await callback.message.answer("Adminga yubormoqchi bo'lgan xabaringizni yozing:")
    await callback.answer()

@dp.message(BotStates.waiting_for_admin_msg)
async def send_to_admin(message: types.Message, state: FSMContext):
    user_info = f"Kimdan: {message.from_user.full_name}\nID: {message.from_user.id}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Javob berish 💬", callback_data=f"reply_{message.from_user.id}")
    
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, f"Yangi xabar!\n\n{user_info}\n\nXabar: {message.text}", 
                                   reply_markup=builder.as_markup())
        except:
            pass
    
    await message.answer("Xabaringiz adminga yetkazildi!")
    await state.clear()

# --- ADMIN JAVOB BERISHI ---
@dp.callback_query(F.data.startswith("reply_"))
async def reply_callback(callback: types.CallbackQuery, state: FSMContext):
    target_id = callback.data.split("_")[1]
    await state.update_data(reply_to=target_id)
    await state.set_state(BotStates.waiting_for_reply_msg)
    await callback.message.answer("Javob matnini yozing:")
    await callback.answer()

@dp.message(BotStates.waiting_for_reply_msg)
async def send_reply_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data['reply_to']
    
    try:
        await bot.send_message(target_id, f"Admin javobi: \n\n{message.text}")
        await message.answer("Javob foydalanuvchiga yuborildi!")
    except Exception as e:
        await message.answer(f"Yuborishda xato: {e}")
    
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
