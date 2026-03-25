import os
import asyncio
import logging
import urllib.parse
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# 1. Логування
logging.basicConfig(level=logging.INFO)

# 2. Токен та ініціалізація
# Порада: на Render додай BOT_TOKEN в Environment Variables
TOKEN = os.environ.get("BOT_TOKEN", "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- КОМАНДИ БОТА ----------------

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 Dryguny 3D Bot\n\n"
        "/find dragon — пошук STL\n"
        "/idea — випадкова модель\n"
        "/trend — трендові моделі\n"
        "/sell — моделі для продажу\n"
        "/filament pla 400-800 — пошук пластику\n"
        "/viral — вірусні моделі\n"
        "/top — топ моделі"
    )

@dp.message(Command("idea"))
async def idea_handler(message: types.Message):
    keywords = ["dragon", "robot", "car", "figurine", "cube", "keychain", "animal", "gadget"]
    keyword = random.choice(keywords)
    q = urllib.parse.quote(keyword)
    text = (
        f"🧠 Ідея: {keyword}\n\n"
        f"MakerWorld: https://makerworld.com/en/search/models?keyword={q}\n"
        f"Printables: https://www.printables.com/search/models?q={q}\n"
        f"Thingiverse: https://www.thingiverse.com/search?q={q}"
    )
    await message.answer(text)

@dp.message(Command("find"))
async def find_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query:
        return await message.answer("❌ Напиши що шукати (наприклад: /find dragon)")
    
    q = urllib.parse.quote(query)
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="MakerWorld", url=f"https://makerworld.com/en/search/models?keyword={q}")],
        [types.InlineKeyboardButton(text="Printables", url=f"https://www.printables.com/search/models?q={q}")],
        [types.InlineKeyboardButton(text="Thingiverse", url=f"https://www.thingiverse.com/search?q={q}")]
    ])
    await message.answer(f"🔎 Пошук STL: {query}", reply_markup=markup)

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):
    try:
        args = message.text.split()
        material = args[1]
        prices = args[2].split("-")
        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={prices[0]}&price_local__lte={prices[1]}"
        await message.answer(f"🧵 Результати філаменту ({material}):\n{url}")
    except:
        await message.answer("❌ Формат: /filament pla 400-800")

@dp.message(Command("trend", "sell", "viral", "top"))
async def combined_handler(message: types.Message):
    # Універсальний обробник для посилань
    urls = "🔥 MakerWorld: https://makerworld.com/en/models\n📦 Printables: https://www.printables.com/model"
    await message.answer(f"Ось корисні посилання:\n\n{urls}")

# ---------------- WEB SERVER (ДЛЯ RENDER) ----------------

async def handle_ping(request):
    return web.Response(text="Bot running")

async def main():
    # Налаштування сервера
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Використовуємо порт від Render
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logging.info(f"✅ Сервер запущено на порту {port}")

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ---------------- ТОЧКА ВХОДУ ----------------

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинений")

    video = random.choice(videos)

    await message.answer(f"🔥 Відео:\n\n{video}")

# ---------------- FILAMENT ----------------
@dp.message(Command("filament"))
async def filament_handler(message: types.Message):

    try:
        args = message.text.split()

        material = args[1]
        price_range = args[2]
        brand = args[3] if len(args) > 3 else ""

        prices = price_range.split("-")

        query = f"{material} filament {brand}".strip()
        q = urllib.parse.quote(query)

        prom_url = f"https://prom.ua/ua/search?search_term={q}&price_local__gte={prices[0]}&price_local__lte={prices[1]}"
        rozetka_url = f"https://rozetka.com.ua/search/?text={q}"

        text = (
            f"🧵 Філамент: {material} {brand}\n"
            f"💰 Ціна: {price_range}\n\n"
            f"Prom.ua:\n{prom_url}\n\n"
            f"Rozetka:\n{rozetka_url}"
        )

        await message.answer(text)

    except:
        await message.answer("❌ Формат: /filament pla 400-800 eSun")

# ---------------- VIRAL ----------------
@dp.message(Command("viral"))
async def viral_handler(message: types.Message):

    text = (
        "🔥 Вірусні моделі:\n\n"
        "TikTok:\nhttps://www.tiktok.com/search?q=3d%20printed\n\n"
        "Flexi dragon:\nhttps://makerworld.com/en/search/models?keyword=flexi%20dragon\n\n"
        "Fidget:\nhttps://makerworld.com/en/search/models?keyword=fidget\n\n"
        "Articulated:\nhttps://makerworld.com/en/search/models?keyword=articulated"
    )

    await message.answer(text)

# ---------------- TOP ----------------
@dp.message(Command("top"))
async def top_handler(message: types.Message):

    text = (
        "🏆 ТОП моделі:\n\n"
        "MakerWorld:\nhttps://makerworld.com/en/models\n\n"
        "Printables:\nhttps://www.printables.com/model?sort=popular\n\n"
        "Thingiverse:\nhttps://www.thingiverse.com/?sort=popular\n\n"
        "Thangs:\nhttps://thangs.com"
    )

    await message.answer(text)

# ---------------- WEB SERVER ----------------
async def handle_ping(request):
    return web.Response(text="Bot running")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()

    await web.TCPSite(
        runner,
        "0.0.0.0",
        int(os.environ.get("PORT", 8080))
    ).start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())    try:
        args = message.text.split()
        material = args[1]
        prices = args[2].split("-")
        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={prices[0]}&price_local__lte={prices[1]}"
        await message.answer(f"🧵 Результати філаменту:\n{url}")
    except:
        await message.answer("❌ Формат: /filament pla 400-800")

# ---------------- WEB SERVER ----------------
async def handle_ping(request):
    return web.Response(text="Bot running")

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
