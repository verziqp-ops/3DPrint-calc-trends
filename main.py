import os
import asyncio
import logging
import urllib.parse
import random
import json

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# --- 1. НАЛАШТУВАННЯ ---
logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN", "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc")
ADMIN_ID = 6259271140 

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_FILE = "products.json"

# Функції для роботи з базою даних (JSON)
def load_products():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

class ShopAdmin(StatesGroup):
    waiting_for_value = State()
    waiting_for_photo = State()

product_drafts = {}

# --- 2. КЛАВІАТУРИ ---

def get_main_keyboard(user_id):
    web_app_url = "https://dryguny.com.ua" 
    buttons = [[KeyboardButton(text="🛍 ВІДКРИТИ МАГАЗИН", web_app=WebAppInfo(url=web_app_url))]]
    
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="📦 Додати товар"), KeyboardButton(text="⚙️ Керувати магазином")])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_edit_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Назва", callback_data="edit_name"), 
         InlineKeyboardButton(text="✏️ Опис", callback_data="edit_desc")],
        [InlineKeyboardButton(text="💰 Ціна", callback_data="edit_price"), 
         InlineKeyboardButton(text="📦 Опт", callback_data="edit_opt")],
        [InlineKeyboardButton(text="📂 Категорія", callback_data="edit_cat")],
        [InlineKeyboardButton(text="🖼 Змінити зображення", callback_data="edit_photo")],
        [InlineKeyboardButton(text="✅ ПІДТВЕРДИТИ ТА В МАГАЗИН", callback_data="confirm_shop")]
    ])

# --- 3. КОМАНДИ ПОШУКУ (ТВОЇ ОРИГІНАЛЬНІ) ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 **Вітаємо у Dryguny 3D Hub!**\n\n"
        "🔍 `/find [назва]` — пошук STL моделей\n"
        "🧠 `/idea` — випадкова ідея\n"
        "🧵 `/filament [тип] [ціна]` — пошук пластику\n"
        "🔥 `/viral` — тренди\n"
        "📈 `/trend` — топ світу",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@dp.message(Command("idea"))
async def idea_handler(message: types.Message):
    keywords = ["dragon", "robot", "car", "figurine", "animal", "fidget", "articulated", "gadget", "container"]
    keyword = random.choice(keywords)
    q = urllib.parse.quote(keyword)
    text = f"🧠 **Ідея для друку:** `{keyword}`\n\n🔗 [MakerWorld](https://makerworld.com/search/models?keyword={q})\n🔗 [Printables](https://www.printables.com/search/models?q={q})\n🔗 [Thingiverse](https://www.thingiverse.com/search?q={q})"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("find"))
async def find_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query: return await message.answer("❌ Напиши, що шукати.")
    q = urllib.parse.quote(query)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="MakerWorld 🧩", url=f"https://makerworld.com/en/search/models?keyword={q}")],
        [InlineKeyboardButton(text="Printables 🟧", url=f"https://www.printables.com/search/models?q={q}")],
        [InlineKeyboardButton(text="Thingiverse 🌀", url=f"https://www.thingiverse.com/search?q={q}")]
    ])
    await message.answer(f"🔎 **Пошук STL для:** `{query}`", reply_markup=markup, parse_mode="Markdown")

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):
    try:
        args = message.text.split()
        material = args[1].lower()
        p_min, p_max = args[2].split("-")
        q_encoded = urllib.parse.quote(material)
        text = f"🧵 **Результати для:** `{material.upper()}`\n💰 Бюджет: `{p_min}-{p_max}` грн\n\n[Filament.org.ua](https://filament.org.ua/ua/product_list?search_term={q_encoded})\n[Prom.ua](https://prom.ua/ua/search?search_term={q_encoded})"
        await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
    except: await message.answer("❌ Формат: `/filament pla 400-600`")

@dp.message(Command("viral"))
async def viral_handler(message: types.Message):
    await message.answer("🔥 **Вірусні моделі:**\n• [TikTok Trends](https://www.tiktok.com/search?q=3d%20printed%20gadgets)", parse_mode="Markdown")

@dp.message(Command("trend", "top"))
async def top_handler(message: types.Message):
    await message.answer("🏆 **ТОП моделі:**\n• [MakerWorld Hot](https://makerworld.com/en/models)", parse_mode="Markdown")

# --- 4. АДМІНІСТРУВАННЯ ТА ВИДАЛЕННЯ ---

@dp.message(F.text == "⚙️ Керувати магазином")
@dp.message(Command("manage"))
async def manage_products(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    products = load_products()
    if not products: return await message.answer("Магазин порожній.")
    
    for idx, p in enumerate(products):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🗑 Видалити", callback_data=f"del_{idx}")]])
        await message.answer(f"📦 **{p['name']}**\nЦіна: {p['price']} грн", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("del_"))
async def delete_product(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    products = load_products()
    if 0 <= idx < len(products):
        removed = products.pop(idx)
        save_products(products)
        await callback.message.edit_text(f"✅ Видалено: {removed['name']}")
    await callback.answer()

# --- 5. ДОДАВАННЯ ТОВАРУ ---

@dp.message(F.text == "📦 Додати товар")
@dp.message(Command("addtoshop"))
async def add_to_shop_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    product_drafts[message.from_user.id] = {
        "name": "Нова 3D Модель", "desc": "Опис...", "price": "0", "opt": "—", "cat": "Інше",
        "img": "https://placehold.jp/600x400.png"
    }
    await send_product_preview(message.chat.id, message.from_user.id)

async def send_product_preview(chat_id, user_id):
    data = product_drafts[user_id]
    caption = f"🏷 **{data['name']}**\n\n{data['desc']}\n\n💰 Ціна: {data['price']} ₴\n📦 Опт: {data['opt']}\n📂 Категорія: {data['cat']}"
    await bot.send_photo(chat_id=chat_id, photo=data['img'], caption=caption, reply_markup=get_edit_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("edit_"))
async def start_editing(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]
    if field == "photo":
        await callback.message.answer("🖼 Надішли фото:")
        await state.set_state(ShopAdmin.waiting_for_photo)
    else:
        await state.update_data(editing_field=field)
        await callback.message.answer(f"Введи нове значення для {field}:")
        await state.set_state(ShopAdmin.waiting_for_value)
    await callback.answer()

@dp.message(ShopAdmin.waiting_for_value)
async def process_text_edit(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    field = (await state.get_data())["editing_field"]
    product_drafts[user_id][field] = message.text
    await state.clear()
    await send_product_preview(message.chat.id, user_id)

@dp.message(ShopAdmin.waiting_for_photo, F.photo)
async def process_photo_edit(message: types.Message, state: FSMContext):
    product_drafts[message.from_user.id]["img"] = message.photo[-1].file_id
    await state.clear()
    await send_product_preview(message.chat.id, message.from_user.id)

@dp.callback_query(F.data == "confirm_shop")
async def confirm_shop(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in product_drafts:
        products = load_products()
        products.append(product_drafts[user_id])
        save_products(products)
        await callback.message.answer("✅ Товар додано в базу!")
        del product_drafts[user_id]
    await callback.answer()

# --- 6. API ДЛЯ САЙТУ ---

async def get_products_api(request):
    return web.json_response(load_products())

async def handle_ping(request):
    return web.Response(text="Dryguny Bot Online")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/get_products", get_products_api) # Посилання для сайту
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
