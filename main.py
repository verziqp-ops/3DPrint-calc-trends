import os
import asyncio
import logging
import urllib.parse
import random
import json
import base64

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
from aiohttp import web

# --- 1. НАЛАШТУВАННЯ ---
logging.basicConfig(level=logging.INFO)

TOKEN = "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc"
GEMINI_KEY = "AIzaSyAkmMTOz4uDgr8hKGTFkNYV2UtXL9GV7qk"
ADMIN_ID = 6259271140 

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class DescGen(StatesGroup):
    waiting_for_input = State()
    waiting_for_price = State()

class ShopAdmin(StatesGroup):
    waiting_for_value = State()
    waiting_for_photo = State()

product_drafts = {}
DB_FILE = "products.json"

# --- МІДЛВЕР ДЛЯ АДМІНА ---
@dp.message.outer_middleware()
async def admin_only_middleware(handler, event: types.Message, data):
    if event.from_user.id != ADMIN_ID: return 
    return await handler(event, data)

# --- 2. ФУНКЦІЯ ШІ (ВИПРАВЛЕНА) ---
async def ask_gemini(prompt, photo_bytes=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    parts = [{"text": prompt}]
    if photo_bytes:
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(photo_bytes).decode('utf-8')
            }
        })

    payload = {"contents": [{"parts": parts}]}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                return f"❌ Помилка сервера ШІ: {resp.status}"
            result = await resp.json()
            try:
                # Чітке витягування тексту
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "❌ Помилка структури відповіді ШІ. Спробуй ще раз."

# --- 3. ЛОГІКА МАГАЗИНУ ---
def load_products():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

# --- 4. КЛАВІАТУРИ (ВИПРАВЛЕНО) ---
def get_main_keyboard():
    # Робимо кнопки у 2 ряди, щоб все було видно
    kb = [
        [KeyboardButton(text="📦 Додати товар"), KeyboardButton(text="⚙️ Керувати магазином")],
        [KeyboardButton(text="📝 Опис для Insta (ШІ)")],
        [KeyboardButton(text="💡 Ідея для друку"), KeyboardButton(text="🔍 Пошук STL")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- 5. ХЕНДЛЕРИ ШІ-ОПИСУ ---

@dp.message(F.text == "📝 Опис для Insta (ШІ)")
@dp.message(Command("description"))
async def desc_start(message: types.Message, state: FSMContext):
    await message.answer("🤖 Надішли назву товару або **фото статуетки**, щоб я її описав!")
    await state.set_state(DescGen.waiting_for_input)

@dp.message(DescGen.waiting_for_input)
async def desc_input(message: types.Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file_info.file_path)
        await state.update_data(photo=photo_bytes.read(), name="статуетка з фото")
        await message.answer("📸 Фото отримано! Яка ціна буде в пості?")
    elif message.text:
        await state.update_data(name=message.text, photo=None)
        await message.answer(f"Назва: {message.text}\nВведи ціну:")
    else:
        return await message.answer("Будь ласка, надішли текст або фото.")
    await state.set_state(DescGen.waiting_for_price)

@dp.message(DescGen.waiting_for_price)
async def desc_final(message: types.Message, state: FSMContext):
    price = message.text
    user_data = await state.get_data()
    wait_msg = await message.answer("⏳ Dryguny AI аналізує модель...")
    
    prompt = (
        f"Напиши пост для Instagram бренду 'Dryguny'. Товар: {user_data.get('name')}. "
        f"Ціна: {price} грн. Дотримуйся шаблону:\n"
        "1. Креативна назва + емодзі\n"
        f"2. {price} грн💵\n"
        "3. Моделі в наявності або виготовлення 1-3 дні📅\n"
        "4. Друк ваших ідей під замовлення✨\n"
        "5. Безпечний пластик PLA♻️\n"
        "Пиши коротко, модно, українською."
    )

    ai_text = await ask_gemini(prompt, user_data.get('photo'))
    await wait_msg.delete()
    await message.answer(f"<code>{ai_text}</code>", parse_mode="HTML")
    await state.clear()

# --- 6. КОМАНДИ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 **Dryguny 3D Hub** активний!\n\nВикористовуй меню нижче для роботи з магазином або генерації постів.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "💡 Ідея для друку")
@dp.message(Command("idea"))
async def idea_handler(message: types.Message):
    keywords = ["dragon", "robot", "cat", "gadget", "figurine"]
    keyword = random.choice(keywords)
    q = urllib.parse.quote(keyword)
    await message.answer(f"🧠 Ідея: **{keyword}**\n🔗 [MakerWorld](https://makerworld.com/search/models?keyword={q})", parse_mode="Markdown")

@dp.message(F.text == "🔍 Пошук STL")
async def find_info(message: types.Message):
    await message.answer("Використовуй команду: `/find назва`", parse_mode="Markdown")

@dp.message(Command("find"))
async def find_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query: return await message.answer("Введи що шукати після команди.")
    q = urllib.parse.quote(query)
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Дивитись на MakerWorld", url=f"https://makerworld.com/en/search/models?keyword={q}")]])
    await message.answer(f"🔎 Моделі для `{query}`:", reply_markup=markup, parse_mode="Markdown")

# --- ЗАПУСК ---
async def handle_ping(request): return web.Response(text="Bot Active")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
