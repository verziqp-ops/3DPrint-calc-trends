import os
import asyncio
import logging
import urllib.parse
import aiohttp
import random
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# --- КОНФІГУРАЦІЯ ШІ ---
GOOGLE_API_KEY = "AIzaSyAkmMTOz4uDgr8hKGTFkNYV2UtXL9GV7qk"
genai.configure(api_key=GOOGLE_API_KEY)

ai_model = genai.GenerativeModel("gemini-1.5-flash")

AI_INSTRUCTION = (
    "Ти — Dryguny AI, асистент бренду Dryguny. "
    "Твій власник — Макс. "
    "Ти експерт у 3D-друці, Bambu Lab та Blender. "
    "Відповідай коротко і з емодзі."
)

# --- КОНФІГУРАЦІЯ БОТА ---
TOKEN = "8594286835:AAEcg2_T6olnaRzFyo45SbRGI-QPiSgAkDo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- START ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 **Dryguny AI Hub v3.4**\n\n"
        "Команди:\n"
        "/help питання — запитати ШІ\n"
        "/find модель — пошук STL\n"
        "/filament pla 400-800 — пошук пластику\n"
        "/trend — трендові моделі",
        parse_mode="Markdown"
    )

# --- AI HELP ---

@dp.message(Command("help"))
async def ai_help_handler(message: types.Message):

    user_query = message.text.replace("/help", "").strip()

    if not user_query:
        await message.answer("🆘 Напиши питання!")
        return

    status_msg = await message.answer("🧠 *Dryguny AI думає...*", parse_mode="Markdown")

    try:

        prompt = f"{AI_INSTRUCTION}\n\nПитання користувача: {user_query}"

        response = await asyncio.to_thread(
            ai_model.generate_content,
            prompt
        )

        answer = response.text if response.text else "⚠️ Модель не дала відповідь."

        await bot.edit_message_text(
            text=f"🤖 **Відповідь:**\n\n{answer}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

    except Exception as e:

        logging.error(f"AI Error: {e}")

        await bot.edit_message_text(
            text="⚠️ Помилка моделі. Спробуй пізніше.",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

# --- ПОШУК STL НА КІЛЬКОХ САЙТАХ ---

@dp.message(Command("find"))
async def find_stl_handler(message: types.Message):

    query = message.text.replace("/find", "").strip()

    if not query:
        return await message.answer("❌ Що шукаємо?")

    q = urllib.parse.quote(query)

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[

            [types.InlineKeyboardButton(
                text="💎 MakerWorld",
                url=f"https://makerworld.com/en/search/models?keyword={q}"
            )],

            [types.InlineKeyboardButton(
                text="🧰 Thingiverse",
                url=f"https://www.thingiverse.com/search?q={q}"
            )],

            [types.InlineKeyboardButton(
                text="🧡 Printables",
                url=f"https://www.printables.com/search/models?q={q}"
            )],

            [types.InlineKeyboardButton(
                text="🔎 Thangs",
                url=f"https://thangs.com/search/{q}"
            )]

        ]
    )

    await message.answer(
        f"🔍 Пошук STL: **{query}**",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- ПОШУК ФІЛАМЕНТУ ---

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):

    try:

        args = message.text.split()

        material = args[1]

        prices = args[2].split("-")

        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={prices[0]}&price_local__lte={prices[1]}"

        await message.answer(
            f"🧵 [Результати на Prom.ua]({url})",
            parse_mode="Markdown"
        )

    except:

        await message.answer(
            "❌ Формат: `/filament pla 400-800`",
            parse_mode="Markdown"
        )

# --- ТРЕНДОВІ МОДЕЛІ ---

@dp.message(Command("trend"))
async def trend_handler(message: types.Message):

    trends = [

        "Articulated Dragon",
        "Flexi Shark",
        "Fidget Cube",
        "Phone Stand",
        "Cable Organizer",
        "Flexi Cat",
        "Mini Octopus",
        "Print-in-place Sword",
        "Gear Spinner",
        "Flexi Rex Dinosaur"
    ]

    model = random.choice(trends)

    q = urllib.parse.quote(model)

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[

            [types.InlineKeyboardButton(
                text="🎬 TikTok пошук",
                url=f"https://www.tiktok.com/search?q=3d%20print%20{q}"
            )],

            [types.InlineKeyboardButton(
                text="💎 MakerWorld",
                url=f"https://makerworld.com/en/search/models?keyword={q}"
            )],

            [types.InlineKeyboardButton(
                text="🧡 Printables",
                url=f"https://www.printables.com/search/models?q={q}"
            )]

        ]
    )

    await message.answer(
        f"🔥 **Трендова модель:**\n\n{model}",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- WEB SERVER ДЛЯ RENDER ---

async def handle_ping(request):
    return web.Response(text="OK")

# --- MAIN ---

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

# --- RUN ---

if __name__ == "__main__":
    asyncio.run(main())
