import os
import asyncio
import logging
import urllib.parse
import aiohttp
import random
import re
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
        "🚀 **Dryguny Hub v6**\n\n"
        "/find модель — пошук STL\n"
        "/trend — трендові моделі\n"
        "/trendvideo — вірусні відео 3D друку\n"
        "/sell — популярні моделі для продажу\n"
        "/idea — випадкова модель\n"
        "/filament pla 400-800 — пошук філаменту",
        parse_mode="Markdown"
    )

# ---------------- FIND STL ----------------

@dp.message(Command("find"))
async def find_stl_handler(message: types.Message):

    query = message.text.replace("/find", "").strip()

    if not query:
        return await message.answer("❌ Що шукаємо?")

    q = urllib.parse.quote(query)

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[

            [types.InlineKeyboardButton(
                text="MakerWorld",
                url=f"https://makerworld.com/en/search/models?keyword={q}"
            )],

            [types.InlineKeyboardButton(
                text="Printables",
                url=f"https://www.printables.com/search/models?q={q}"
            )],

            [types.InlineKeyboardButton(
                text="Thingiverse",
                url=f"https://www.thingiverse.com/search?q={q}"
            )],

            [types.InlineKeyboardButton(
                text="Thangs",
                url=f"https://thangs.com/search/{q}"
            )]

        ]
    )

    await message.answer(
        f"🔎 Пошук STL: **{query}**",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ---------------- FILAMENT ----------------

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):

    try:

        args = message.text.split()

        material = args[1]

        prices = args[2].split("-")

        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={prices[0]}&price_local__lte={prices[1]}"

        await message.answer(
            f"🧵 [Результати філаменту]({url})",
            parse_mode="Markdown"
        )

    except:

        await message.answer("❌ Формат: `/filament pla 400-800`")

# ---------------- PARSE MAKERWORLD ----------------

async def get_models():

    url = "https://makerworld.com/en/models"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()

    models = re.findall(r'/en/models/(\d+)', html)

    models = list(dict.fromkeys(models))

    return models

# ---------------- TREND ----------------

@dp.message(Command("trend"))
async def trend_handler(message: types.Message):

    try:

        models = await get_models()

        models = models[:6]

        buttons = []

        for m in models:

            link = f"https://makerworld.com/en/models/{m}"

            buttons.append([
                types.InlineKeyboardButton(
                    text=f"🔥 Тренд {m}",
                    url=link
                )
            ])

        markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(
            "🔥 **Трендові моделі:**",
            parse_mode="Markdown",
            reply_markup=markup
        )

    except:

        await message.answer("⚠️ Не вдалося отримати тренди.")

# ---------------- SELL ----------------

@dp.message(Command("sell"))
async def sell_handler(message: types.Message):

    try:

        models = await get_models()

        models = models[:5]

        buttons = []

        for m in models:

            link = f"https://makerworld.com/en/models/{m}"

            buttons.append([
                types.InlineKeyboardButton(
                    text=f"💰 Модель {m}",
                    url=link
                )
            ])

        markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(
            "💰 **Популярні моделі для продажу:**",
            parse_mode="Markdown",
            reply_markup=markup
        )

    except:

        await message.answer("⚠️ Помилка пошуку моделей.")

# ---------------- IDEA ----------------

@dp.message(Command("idea"))
async def idea_handler(message: types.Message):

    try:

        models = await get_models()

        model = random.choice(models)

        link = f"https://makerworld.com/en/models/{model}"

        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="🧠 Подивитись модель",
                    url=link
                )]
            ]
        )

        await message.answer(
            "🧠 **Ідея для друку:**",
            parse_mode="Markdown",
            reply_markup=markup
        )

    except:

        await message.answer("⚠️ Не вдалося знайти модель.")

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

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="🎬 Подивитись відео",
                url=video
            )]
        ]
    )

    await message.answer(
        "🔥 **Вірусні відео 3D друку:**",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ---------------- WEB SERVER ----------------

async def handle_ping(request):
    return web.Response(text="OK")

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
    asyncio.run(main())
