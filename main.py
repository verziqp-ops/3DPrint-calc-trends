import os, asyncio, logging, urllib.parse, aiohttp
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# ТОКЕН (краще онови через BotFather і встав сюди новий)
TOKEN = "8594286835:AAGh9mfOe-e0Bufwtprao4uBYHTOQRnsWwo" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 1. СТАРТ
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🛠 **Dryguny Hub v2.0**\n\n"
        "🔍 `/find назва` — пошук STL\n"
        "🧵 `/filament тип ціна-ціна` — пошук пластику\n"
        "🆘 `/help проблема` — поради з друку\n"
        "🔥 `/trends` — тренди",
        parse_mode="Markdown")

# 2. ПОШУК STL
@dp.message(Command("find"))
async def find_stl(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query: return await message.answer("Напиши що шукати: `/find dragon`")
    
    q = urllib.parse.quote(query)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💎 MakerWorld", url=f"https://makerworld.com/en/models/search?keyword={q}")],
        [types.InlineKeyboardButton(text="🧩 Printables", url=f"https://www.printables.com/search/models?q={q}")]
    ])
    await message.answer(f"🔍 Шукаю STL: **{query}**", reply_markup=kb, parse_mode="Markdown")

# 3. ПОШУК ФІЛАМЕНТУ
@dp.message(Command("filament"))
async def filament_search(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 3: return await message.answer("Формат: `/filament pla 400-800`")
        
        material, p_range = args[1].lower(), args[2].split("-")
        min_p, max_p = p_range[0], p_range[1]
        
        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={min_p}&price_local__lte={max_p}"
        await message.answer(f"🧵 Пошук {material} ({min_p}-{max_p} грн):\n[Відкрити результати на Prom.ua]({url})", parse_mode="Markdown")
    except:
        await message.answer("⚠️ Помилка. Приклад: `/filament petg 500-900`")

# 4. ТРЕНДИ
@dp.message(Command("trends"))
async def trends(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔥 MakerWorld", url="https://makerworld.com/uk")],
        [types.InlineKeyboardButton(text="🎬 TikTok Ideas", url="https://www.tiktok.com/search/video?q=3d%20printing%20ideas")]
    ])
    await message.answer("🚀 Трендові моделі:", reply_markup=kb)

# 5. ДОПОМОГА
@dp.message(Command("help"))
async def fix_help(message: types.Message):
    prob = message.text.replace("/help", "").lower()
    if "липне" in prob:
        msg = "🛠 **Не липне?**\n1. Помий стіл.\n2. Перевір Z-offset.\n3. Спробуй клей-олівець."
    elif "павутина" in prob:
        msg = "🛠 **Павутина?**\n1. Зменш температуру сопла.\n2. Збільш ретракт.\n3. Просуши пластик."
    else:
        msg = "🛠 Опиши проблему після команди, наприклад: `/help павутина`"
    await message.answer(msg, parse_mode="Markdown")

# ВАЖЛИВО: Ехо-handler має бути в самому кінці!
@dp.message()
async def echo(message: types.Message):
    await message.answer("Я не знаю такої команди. Спробуй /start")

# --- СЕРВЕР ---
async def handle_ping(r): return web.Response(text="Running")
async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
