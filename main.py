import os
import asyncio
import logging
import urllib.parse
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# 1. НАЛАШТУВАННЯ ЛОГУВАННЯ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. ІНІЦІАЛІЗАЦІЯ БОТА
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    TOKEN = "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- КОМАНДИ БОТА ----------------

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 **Вітаємо у Dryguny 3D Hub!**\n\n"
        "Твій інструмент для швидкого пошуку моделей та пластику:\n\n"
        "🔍 `/find [назва]` — швидкий пошук STL моделей\n"
        "🧠 `/idea` — випадкова ідея для наступного друку\n"
        "🧵 `/filament [тип] [ціна]` — пошук пластику (напр. `/filament pla 300-600`)\n"
        "🔥 `/viral` — вірусні та трендові моделі\n"
        "📈 `/trend` — що зараз популярно у світі 3D",
        parse_mode="Markdown"
    )

@dp.message(Command("idea"))
async def idea_handler(message: types.Message):
    keywords = ["dragon", "robot", "car", "figurine", "animal", "fidget", "articulated", "gadget", "container"]
    keyword = random.choice(keywords)
    q = urllib.parse.quote(keyword)
    text = (
        f"🧠 **Ідея для друку:** `{keyword}`\n\n"
        f"🔗 [MakerWorld](https://makerworld.com/search/models?keyword={q})\n"
        f"🔗 [Printables](https://www.printables.com/search/models?q={q})\n"
        f"🔗 [Thingiverse](https://www.thingiverse.com/search?q={q})"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=False)

@dp.message(Command("find"))
async def find_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query:
        return await message.answer("❌ Напиши, що саме шукати. Наприклад: `/find dragon`", parse_mode="Markdown")
    
    q = urllib.parse.quote(query)
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="MakerWorld 🧩", url=f"https://makerworld.com/en/search/models?keyword={q}")],
        [types.InlineKeyboardButton(text="Printables 🟧", url=f"https://www.printables.com/search/models?q={q}")],
        [types.InlineKeyboardButton(text="Thingiverse 🌀", url=f"https://www.thingiverse.com/search?q={q}")]
    ])
    await message.answer(f"🔎 **Пошук STL для:** `{query}`", reply_markup=markup, parse_mode="Markdown")

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            return await message.answer("❌ Формат: `/filament [тип] [ціна_мін-макс]`\nПриклад: `/filament pla 400-600`", parse_mode="Markdown")

        material = args[1].lower()
        price_range = args[2]
        p_min, p_max = price_range.split("-")
        q_encoded = urllib.parse.quote(material)

        categories = {
            "pla": "g129478502-pla",
            "petg": "g129479663-petg-copet",
            "abs": "g133329867-abs",
            "tpu": "g130517258-tpu",
            "silk": "g133705086-pla-silk",
            "wood": "g148300313-wood-pla"
        }

        cat_path = categories.get(material, "product_list")
        if cat_path != "product_list":
            filament_ua_url = f"https://filament.org.ua/ua/{cat_path}?price_unit__lte={p_max}&price_unit__gte={p_min}"
        else:
            filament_ua_url = f"https://filament.org.ua/ua/product_list?search_term={q_encoded}&price_unit__lte={p_max}&price_unit__gte={p_min}"

        google_url = f"https://www.google.com/search?q={q_encoded}+філамент+купити+{p_min}..{p_max}+грн"
        prom_url = f"https://prom.ua/ua/search?search_term={q_encoded}+filament&price_local__gte={p_min}&price_local__lte={p_max}"
        rozetka_url = f"https://rozetka.com.ua/search/?text={q_encoded}+filament&price={p_min}-{p_max}"

        text = (
            f"🧵 **Результати для:** `{material.upper()}`\n"
            f"💰 Бюджет: `{p_min} — {p_max}` грн\n\n"
            f"🔥 [Filament.org.ua]({filament_ua_url})\n"
            f"🟨 [Prom.ua]({prom_url})\n"
            f"🟦 [Rozetka]({rozetka_url})\n"
            f"🌐 [Google Пошук]({google_url})"
        )
        await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await message.answer("❌ Помилка! Формат: `/filament pla 300-500`", parse_mode="Markdown")

@dp.message(Command("viral"))
async def viral_handler(message: types.Message):
    text = (
        "🔥 **Вірусні моделі для твого каналу:**\n\n"
        "• [TikTok Trends](https://www.tiktok.com/search?q=3d%20printed%20gadgets)\n"
        "• [Flexi Animals](https://makerworld.com/en/search/models?keyword=flexi)\n"
        "• [Fidget & Stress Relief](https://makerworld.com/en/search/models?keyword=fidget)"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("trend", "top"))
async def top_handler(message: types.Message):
    text = (
        "🏆 **ТОП моделі з усього світу:**\n\n"
        "• [MakerWorld Hot](https://makerworld.com/en/models)\n"
        "• [Printables Popular](https://www.printables.com/model?sort=popular)\n"
        "• [Thangs (3D Search Engine)](https://thangs.com)"
    )
    await message.answer(text, parse_mode="Markdown")

# ---------------- ВЕБ-СЕРВЕР ТА ЗАПУСК ----------------

async def handle_ping(request):
    return web.Response(text="Dryguny Bot is Running! 🚀")

async def main():
    # Налаштовуємо веб-сервер для Render (Keep-alive)
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ Web server is live on port {port}")

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        logger.info("🚀 Starting Bot Polling...")
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинений")
