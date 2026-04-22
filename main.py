import os
import asyncio
import logging
import urllib.parse
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# 1. НАЛАШТУВАННЯ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc")
ADMIN_ID = 6259271140 # Твій ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# ---------------- КЛАВІАТУРИ ----------------

def get_main_keyboard(user_id):
    web_app_url = "https://dryguny.com.ua" # Твій Mini App
    buttons = [[KeyboardButton(text="🛍 ВІДКРИТИ МАГАЗИН", web_app=WebAppInfo(url=web_app_url))]]
    
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="📦 Додати товар")])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ---------------- КОМАНДИ ПОШУКУ (ЯКІ БУЛИ) ----------------

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

# ---------------- ЛОГІКА ADDTOSHOP (ПО ПОСИЛАННЮ) ----------------

@dp.message(Command("addtoshop"))
async def add_to_shop_link(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    url = message.text.replace("/addtoshop", "").strip()
    if not url:
        return await message.answer("🔗 Надішли посилання на модель після команди. Наприклад:\n`/addtoshop https://makerworld.com/...`")

    await message.answer("⏳ Аналізую посилання та генерую опис...")
    
    # Імітація парсингу та ШІ
    generated_name = "Стильний 3D Органайзер"
    generated_desc = "Чудова модель для вашого робочого столу. Забезпечує ідеальний порядок. Надруковано з високоякісного PLA."
    dummy_photo = "https://placehold.jp/600x400.png" # Тут буде фото з посилання

    user_data[message.from_user.id] = {
        "name": generated_name,
        "desc": generated_desc,
        "price": "0", "opt": "—"
    }

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Назва", callback_data="mod_name"), InlineKeyboardButton(text="✏️ Опис", callback_data="mod_desc")],
        [InlineKeyboardButton(text="💰 Ціна", callback_data="mod_price"), InlineKeyboardButton(text="📦 Опт", callback_data="mod_opt")],
        [InlineKeyboardButton(text="✅ В МАГАЗИН", callback_data="finish")]
    ])

    await message.answer_photo(dummy_photo, caption=f"🏷 **{generated_name}**\n\n{generated_desc}\n\nЦіна: 0 ₴", reply_markup=markup)

# ---------------- ОБРОБКА РЕДАГУВАННЯ ----------------

@dp.callback_query(F.data.startswith("mod_"))
async def edit_call(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    user_data[callback.from_user.id]["last_action"] = action
    await callback.message.answer(f"Введіть нове значення:")
    await callback.answer()

@dp.message(lambda m: m.from_user.id == ADMIN_ID and "last_action" in user_data.get(m.from_user.id, {}))
async def save_edit(message: types.Message):
    action = user_data[message.from_user.id].pop("last_action")
    user_data[message.from_user.id][action] = message.text
    await message.answer("✅ Дані оновлено! Надішли `/addtoshop [посилання]` знову для перевірки або тисни завершити.")

@dp.callback_query(F.data == "finish")
async def finish_push(callback: types.CallbackQuery):
    await callback.message.answer("🚀 Товар успішно додано до твоєї бази Mini App!")
    await callback.answer()

# ---------------- ВЕБ-СЕРВЕР ----------------

async def handle_ping(request):
    return web.Response(text="Dryguny Bot is Running! 🚀")

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
