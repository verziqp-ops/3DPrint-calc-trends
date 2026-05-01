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

# Твій токен бота та ключ Gemini
TOKEN = "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc"
GEMINI_KEY = "AIzaSyAkmMTOz4uDgr8hKGTFkNYV2UtXL9GV7qk"
ADMIN_ID = 6259271140 

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Стан для генератора описів
class DescGen(StatesGroup):
    waiting_for_input = State()
    waiting_for_price = State()

# Стан для адмінки магазину
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

# --- 2. ФУНКЦІЯ ШІ (GEMINI) ---
async def ask_gemini(prompt, photo_bytes=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    if photo_bytes:
        payload["contents"][0]["parts"].append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(photo_bytes).decode('utf-8')
            }
        })

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except:
                return "❌ Помилка: ШІ не зміг згенерувати опис. Перевір ключ або з'єднання."

# --- 3. ЛОГІКА МАГАЗИНУ (JSON) ---
def load_products():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

# --- 4. КЛАВІАТУРИ ---
def get_main_keyboard():
    kb = [
        [KeyboardButton(text="📦 Додати товар"), KeyboardButton(text="⚙️ Керувати магазином")],
        [KeyboardButton(text="📝 Опис для Insta (ШІ)")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_edit_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Назва", callback_data="edit_name"), InlineKeyboardButton(text="💰 Ціна", callback_data="edit_price")],
        [InlineKeyboardButton(text="🖼 Фото", callback_data="edit_photo")],
        [InlineKeyboardButton(text="✅ ПІДТВЕРДИТИ", callback_data="confirm_shop")]
    ])

# --- 5. ХЕНДЛЕРИ ШІ-ОПИСУ ---

@dp.message(F.text == "📝 Опис для Insta (ШІ)")
@dp.message(Command("description"))
async def desc_start(message: types.Message, state: FSMContext):
    await message.answer("🤖 Надішліть назву товару або **фото** (я сам зрозумію, що це)!")
    await state.set_state(DescGen.waiting_for_input)

@dp.message(DescGen.waiting_for_input)
async def desc_input(message: types.Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file_info.file_path)
        await state.update_data(photo=photo_bytes.read(), name="з фото")
        await message.answer("📸 Фото отримано! Тепер вкажи ціну (цифрами):")
    else:
        await state.update_data(name=message.text, photo=None)
        await message.answer(f"Назва: {message.text}\nВкажи ціну для посту:")
    
    await state.set_state(DescGen.waiting_for_price)

@dp.message(DescGen.waiting_for_price)
async def desc_final(message: types.Message, state: FSMContext):
    price = message.text
    user_data = await state.get_data()
    wait_msg = await message.answer("⏳ ШІ аналізує та пише опис...")
    
    prompt = (
        f"Ти копірайтер для бренду 3D друку 'Dryguny'. Напиши пост в Instagram. "
        f"Товар: {user_data.get('name')}. Ціна: {price} грн. "
        f"Використовуй цей шаблон ТОЧНО:\n"
        "1. Назва товару та крутий емодзі\n"
        f"2. {price} грн💵\n"
        "3. Зазвичай моделі є в наявності або виготовлення 1-3 дні📅\n"
        "4. Можемо надрукувати ваші ідеї (не з нашого асортименту)✨\n"
        "5. Надруковано з безпечного для здоров'я екологічного пластику PLA♻️\n"
        "Пиши українською. Якщо є фото, опиши що на ньому бачиш коротко і привабливо."
    )

    ai_text = await ask_gemini(prompt, user_data.get('photo'))
    await wait_msg.delete()
    await message.answer(f"<code>{ai_text}</code>", parse_mode="HTML")
    await state.clear()

# --- 6. КОМАНДИ ПОШУКУ ТА ІДЕЙ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("🚀 **Dryguny 3D Hub** активний!", reply_markup=get_main_keyboard(), parse_mode="Markdown")

@dp.message(Command("find"))
async def find_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query: return await message.answer("❌ Що шукаємо?")
    q = urllib.parse.quote(query)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="MakerWorld 🧩", url=f"https://makerworld.com/en/search/models?keyword={q}")],
        [InlineKeyboardButton(text="Printables 🟧", url=f"https://www.printables.com/search/models?q={q}")]
    ])
    await message.answer(f"🔎 Пошук моделей для: `{query}`", reply_markup=markup, parse_mode="Markdown")

# --- 7. КЕРУВАННЯ ТА ДОДАВАННЯ (Твій оригінальний код) ---

@dp.message(F.text == "⚙️ Керувати магазином")
async def manage_products(message: types.Message):
    products = load_products()
    if not products: return await message.answer("Магазин порожній.")
    for idx, p in enumerate(products):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🗑 Видалити", callback_data=f"del_{idx}")]])
        await message.answer(f"📦 **{p.get('name')}** - {p.get('price')} грн", reply_markup=kb)

@dp.callback_query(F.data.startswith("del_"))
async def delete_product(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    products = load_products()
    if 0 <= idx < len(products):
        products.pop(idx)
        save_products(products)
        await callback.message.delete()
    await callback.answer("Видалено")

@dp.message(F.text == "📦 Додати товар")
async def add_to_shop(message: types.Message):
    product_drafts[message.from_user.id] = {"name": "Нова модель", "desc": "Опис...", "price": "0", "img": "https://placehold.jp/600x400.png", "opt": "-", "cat": "-"}
    await send_preview(message.chat.id, message.from_user.id)

async def send_preview(chat_id, user_id):
    data = product_drafts[user_id]
    caption = f"🏷 {data['name']}\n💰 {data['price']} грн"
    await bot.send_photo(chat_id, data['img'], caption=caption, reply_markup=get_edit_keyboard())

# --- 8. ЗАПУСК ---

async def handle_ping(request): return web.Response(text="Online")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
