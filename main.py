import os
import asyncio
import logging
import urllib.parse
import random
import json
import base64

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import google.generativeai as genai

# --- 1. НАЛАШТУВАННЯ (БЕЗПЕЧНЕ) ---
logging.basicConfig(level=logging.INFO)

# Отримуємо ключі з оточення Render
TOKEN = os.getenv("BOT_TOKEN", "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc")
GEMINI_KEY = os.getenv("GEMINI_KEY", "AIzaSyAkmMTOz4uDgr8hKGTFkNYV2UtXL9GV7qk")
ADMIN_ID = 6259271140 

# Налаштування Gemini через офіційну бібліотеку
genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class DescGen(StatesGroup):
    waiting_for_input = State()
    waiting_for_price = State()

# --- 2. ФУНКЦІЯ ШІ (ОПТИМІЗОВАНА) ---
async def ask_gemini(prompt, photo_bytes=None):
    try:
        content = []
        if photo_bytes:
            content.append({
                "mime_type": "image/jpeg",
                "data": photo_bytes
            })
        content.append(prompt)

        # Запуск у фоновому потоці для Render
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: gemini_model.generate_content(content))
        
        return response.text if response.text else "❌ ШІ не зміг згенерувати опис."
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        return f"❌ Помилка ШІ: Перевірте API ключ в налаштуваннях Render."

# --- 3. КЛАВІАТУРА ---
def get_main_keyboard():
    kb = [
        [KeyboardButton(text="📦 Додати товар"), KeyboardButton(text="⚙️ Керувати магазином")],
        [KeyboardButton(text="📝 Опис для Insta (ШІ)")],
        [KeyboardButton(text="💡 Ідея для друку"), KeyboardButton(text="🔍 Пошук STL")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- 4. ХЕНДЛЕРИ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 **Dryguny 3D Hub** готовий до роботи!",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "📝 Опис для Insta (ШІ)")
async def desc_start(message: types.Message, state: FSMContext):
    await message.answer("🤖 Надішли назву або **фото**, щоб я створив пост!")
    await state.set_state(DescGen.waiting_for_input)

@dp.message(DescGen.waiting_for_input)
async def desc_input(message: types.Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_data = await bot.download_file(file_info.file_path)
        # Зберігаємо байти для Gemini
        await state.update_data(photo=photo_data.read(), name="модель з фото")
        await message.answer("📸 Фото отримано! Вкажіть ціну:")
    elif message.text:
        await state.update_data(name=message.text, photo=None)
        await message.answer(f"Назва: {message.text}\nВведіть ціну:")
    await state.set_state(DescGen.waiting_for_price)

@dp.message(DescGen.waiting_for_price)
async def desc_final(message: types.Message, state: FSMContext):
    price = message.text
    user_data = await state.get_data()
    wait_msg = await message.answer("⏳ Dryguny AI чаклує над описом...")
    
    prompt = (
        f"Ти копірайтер бренду 'Dryguny'. Напиши пост в Instagram. "
        f"Товар: {user_data.get('name')}. Ціна: {price} грн. "
        "Структура: 1. Назва+емодзі. 2. Ціна. 3. Терміни (1-3 дні). "
        "4. Заклик до замовлення. 5. Хештеги #dryguny #3dprint. "
        "Стиль: сучасний, українською."
    )

    ai_text = await ask_gemini(prompt, user_data.get('photo'))
    await wait_msg.delete()
    await message.answer(f"<code>{ai_text}</code>", parse_mode="HTML")
    await state.clear()

# --- ДОДАТКОВІ ФУНКЦІЇ ---

@dp.message(F.text == "💡 Ідея для друку")
async def idea_handler(message: types.Message):
    ideas = ["Dinosaur", "Phone Stand", "Articulated Dragon", "Tool Organizer"]
    keyword = random.choice(ideas)
    url = f"https://makerworld.com/search/models?keyword={urllib.parse.quote(keyword)}"
    await message.answer(f"💡 Ідея: **{keyword}**\n🔗 [Шукати на MakerWorld]({url})", parse_mode="Markdown")

# --- ЗАПУСК ВЕБ-СЕРВЕРА ТА БОТА ---
async def handle_ping(request):
    return web.Response(text="Bot is running")

async def main():
    # Налаштування веб-сервера для Render
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
