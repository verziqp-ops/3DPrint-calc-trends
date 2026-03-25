import os
import asyncio
import logging
import urllib.parse
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

logging.basicConfig(level=logging.INFO)

TOKEN = "8594286835:AAEDHt153sAHcHnYoc44IBcOlGZUV1u8-6k"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- START ----------------
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 Dryguny 3D Bot\n\n"
        "/find dragon — пошук STL\n"
        "/idea — випадкова модель\n"
        "/trend — трендові моделі\n"
        "/sell — моделі для продажу\n"
        "/trendvideo — вірусні відео\n"
        "/filament pla 400-800 eSun — філамент\n"
        "/viral — вірусні моделі\n"
        "/top — топ моделі"
    )

# ---------------- IDEA ----------------
@dp.message(Command("idea"))
async def idea_handler(message: types.Message):
    keywords = ["dragon", "robot", "car", "figurine", "cube", "keychain", "animal", "gadget"]
    keyword = random.choice(keywords)
    q = urllib.parse.quote(keyword)

    text = (
        f"🧠 Ідея: {keyword}\n\n"
        f"MakerWorld:\nhttps://makerworld.com/en/search/models?keyword={q}\n\n"
        f"Printables:\nhttps://www.printables.com/search/models?q={q}\n\n"
        f"Thingiverse:\nhttps://www.thingiverse.com/search?q={q}\n\n"
        f"Thangs:\nhttps://thangs.com/search/{q}"
    )

    await message.answer(text)

# ---------------- TREND ----------------
@dp.message(Command("trend"))
async def trend_handler(message: types.Message):

    text = (
        "🔥 Трендові моделі:\n\n"
        "MakerWorld:\nhttps://makerworld.com/en/models\n\n"
        "Printables:\nhttps://www.printables.com/model?period=week&sort=trending\n\n"
        "Thingiverse:\nhttps://www.thingiverse.com/?sort=popular\n\n"
        "TikTok:\nhttps://www.tiktok.com/search?q=3d%20print"
    )

    await message.answer(text)

# ---------------- SELL ----------------
@dp.message(Command("sell"))
async def sell_handler(message: types.Message):

    text = (
        "💰 Що продавати:\n\n"
        "Flexi toys:\nhttps://makerworld.com/en/search/models?keyword=flexi\n\n"
        "Keychains:\nhttps://makerworld.com/en/search/models?keyword=keychain\n\n"
        "Phone stands:\nhttps://makerworld.com/en/search/models?keyword=phone%20stand\n\n"
        "Fidget toys:\nhttps://makerworld.com/en/search/models?keyword=fidget\n\n"
        "TikTok:\nhttps://www.tiktok.com/search?q=3d%20printed%20toys"
    )

    await message.answer(text)

# ---------------- FIND ----------------
@dp.message(Command("find"))
async def find_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()

    if not query:
        return await message.answer("❌ Напиши що шукати")

    q = urllib.parse.quote(query)

    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="MakerWorld", url=f"https://makerworld.com/en/search/models?keyword={q}")],
        [types.InlineKeyboardButton(text="Printables", url=f"https://www.printables.com/search/models?q={q}")],
        [types.InlineKeyboardButton(text="Thingiverse", url=f"https://www.thingiverse.com/search?q={q}")],
        [types.InlineKeyboardButton(text="Thangs", url=f"https://thangs.com/search/{q}")]
    ])

    await message.answer(f"🔎 Пошук STL: {query}", reply_markup=markup)

# ---------------- TREND VIDEO ----------------
@dp.message(Command("trendvideo"))
async def trendvideo_handler(message: types.Message):

    videos = [
        "https://www.tiktok.com/search?q=3d%20print",
        "https://www.youtube.com/results?search_query=3d+printing+viral",
        "https://www.youtube.com/results?search_query=3d+print+timelapse",
        "https://www.tiktok.com/search?q=3d%20printed%20dragon"
    ]

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
