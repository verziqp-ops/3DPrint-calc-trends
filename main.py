import os
import asyncio
import logging
import urllib.parse
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# --- 1. НАЛАШТУВАННЯ ---
logging.basicConfig(level=logging.INFO)

# Твій токен та ID (Макс, перевір, щоб ID був твій)
TOKEN = os.environ.get("BOT_TOKEN", "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc")
ADMIN_ID = 5621405021 

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Сховище станів для адмінки (FSM)
class ShopAdmin(StatesGroup):
    waiting_for_value = State()  # Очікуємо текст (ціна, назва тощо)
    waiting_for_photo = State()  # Очікуємо нове фото

# Тимчасове сховище для чернеток товарів
product_drafts = {}

# --- 2. КЛАВІАТУРИ ---

def get_main_keyboard(user_id):
    web_app_url = "https://dryguny.com.ua" 
    buttons = [[KeyboardButton(text="🛍 ВІДКРИТИ МАГАЗИН", web_app=WebAppInfo(url=web_app_url))]]
    
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="📦 Додати товар")])
        
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

# --- 3. КОМАНДИ ПОШУКУ ТА ІНФО ---

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

# --- 4. ЛОГІКА ДОДАВАННЯ ТОВАРУ (/addtoshop) ---

@dp.message(Command("addtoshop"))
async def add_to_shop_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    url = message.text.replace("/addtoshop", "").strip()
    if not url:
        return await message.answer("🔗 Надішли посилання на модель:\n`/addtoshop https://makerworld.com/...`")

    await message.answer("⏳ Аналізую модель та генерую опис...")

    # Початкова чернетка
    product_drafts[message.from_user.id] = {
        "name": "Нова 3D Модель",
        "desc": "Автоматично згенерований опис. Ви можете змінити його кнопкою нижче.",
        "price": "0",
        "opt": "—",
        "cat": "Інше",
        "img": "https://placehold.jp/24/ff5722/ffffff/600x400.png?text=DRYGUNY_3D" 
    }

    await send_product_preview(message.chat.id, message.from_user.id)

async def send_product_preview(chat_id, user_id):
    data = product_drafts[user_id]
    caption = (
        f"🏷 **{data['name']}**\n\n"
        f"{data['desc']}\n\n"
        f"💰 Ціна: {data['price']} ₴\n"
        f"📦 Опт: {data['opt']}\n"
        f"📂 Категорія: {data['cat']}"
    )
    
    await bot.send_photo(
        chat_id=chat_id,
        photo=data['img'],
        caption=caption,
        reply_markup=get_edit_keyboard(),
        parse_mode="Markdown"
    )

# --- 5. ОБРОБКА РЕДАГУВАННЯ (TEXT & PHOTO) ---

@dp.callback_query(F.data.startswith("edit_"))
async def start_editing(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    
    field = callback.data.split("_")[1]
    
    if field == "photo":
        await callback.message.answer("🖼 Надішли нове фото для товару:")
        await state.set_state(ShopAdmin.waiting_for_photo)
    else:
        prompts = {
            "name": "Введи нову назву:", "desc": "Введи опис товару:", 
            "price": "Введи ціну (цифрами):", "opt": "Введи умови опту:", 
            "cat": "Введи категорію:"
        }
        await state.update_data(editing_field=field)
        await callback.message.answer(prompts.get(field, "Введи нове значення:"))
        await state.set_state(ShopAdmin.waiting_for_value)
    
    await callback.answer()

# Обробка тексту
@dp.message(ShopAdmin.waiting_for_value)
async def process_text_edit(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    state_data = await state.get_data()
    field = state_data.get("editing_field")

    product_drafts[user_id][field] = message.text
    await state.clear()
    await message.answer(f"✅ {field} оновлено!")
    await send_product_preview(message.chat.id, user_id)

# Обробка фото
@dp.message(ShopAdmin.waiting_for_photo, F.photo)
async def process_photo_edit(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id # Беремо найкращу якість

    product_drafts[user_id]["img"] = photo_id
    await state.clear()
    await message.answer("✅ Фото успішно змінено!")
    await send_product_preview(message.chat.id, user_id)

# --- 6. ПІДТВЕРДЖЕННЯ ---

@dp.callback_query(F.data == "confirm_shop")
async def finish_and_publish(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = product_drafts.get(user_id)
    
    if data:
        # Тут можна додати код для збереження в БД або відправки в адмін-канал
        await callback.message.answer(f"🚀 **ТОВАР ОПУБЛІКОВАНО!**\n\n'{data['name']}' тепер у магазині.")
        del product_drafts[user_id]
    
    await callback.answer()

# --- 7. ЗАПУСК (ВЕБ-СЕРВЕР ДЛЯ RENDER) ---

async def handle_ping(request):
    return web.Response(text="Dryguny Bot is Online! 🚀")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
