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

# 2. ІНІЦІАЛІЗАЦІЯ БОТА
# Токен обов'язково додай у "Environment Variables" на Render з назвою BOT_TOKEN
TOKEN = os.environ.get("BOT_TOKEN", "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc")
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
        "🏆 `/top` — найкращі моделі з популярних сайтів\n"
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
        f"🔗 [MakerWorld](https://makerworld.com/en/search/models?keyword={q})\n"
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
        # Очікуємо формат: /filament pla 300-500
        args = message.text.split()
        if len(args) < 3:
            return await message.answer("❌ Неправильний формат! Спробуй так:\n`/filament pla 300-500`", parse_mode="Markdown")

        material = args[1].lower()
        price_range = args[2]
        
        # Обробка ціни для фільтрів
        prices = price_range.split("-")
        min_p = prices[0]
        max_p = prices[1]

        # 1. Google запит (широкий пошук)
        google_query = f"{material} філамент купити ціна {max_p} грн"
        g_url = f"https://www.google.com/search?q={urllib.parse.quote(google_query)}"

        # 2. Prom.ua (з точним фільтром ціни)
        prom_url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={min_p}&price_local__lte={max_p}"

        # 3. Rozetka
        rozetka_url = f"https://rozetka.com.ua/search/?text={material}+filament"

        # 4. Спеціалізований магазин (3DShop)
        shop3d_url = f"https://3dshop.com.ua/search/?search={material}"

        text = (
            f"🧵 **Результати для філаменту:** `{material.upper()}`\n"
            f"💰 Твій бюджет: `{price_range}` грн\n\n"
            f"🌍 [Усі результати в Google]({g_url})\n"
            f"🟨 [Шукати на Prom.ua (з ціною)]({prom_url})\n"
            f"🟦 [Шукати на Rozetka]({rozetka_url})\n"
            f"🚀 [Магазин 3DShop.com.ua]({shop3d_url})"
        )

        await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await message.answer("❌ Помилка! Формат має бути: `/filament pla 300-500`", parse_mode="Markdown")

@dp.message(Command("viral"))
async def viral_handler(message: types.Message):
    text = (
        "🔥 **Вірусні моделі для твого каналу:**\n\n"
        "• [TikTok Trends](https://www.tiktok.com/search?q=3d%20printed%20gadgets)\n"
        "• [Flexi Animals](https://makerworld.com/en/search/models?keyword=flexi)\n"
        "• [Fidgets & Stress Relief](https://makerworld.com/en/search/models?keyword=fidget)\n"
        "• [Articulated Models](https://makerworld.com/en/search/models?keyword=articulated)"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("top", "trend"))
async def top_handler(message: types.Message):
    text = (
        "🏆 **ТОП моделі з усього світу:**\n\n"
        "• [MakerWorld (Bambu Lab)](https://makerworld.com/en/models)\n"
        "• [Printables Popular](https://www.printables.com/model?sort=popular)\n"
        "• [Thingiverse Hot](https://www.thingiverse.com/?sort=popular)\n"
        "• [Thangs (3D Search Engine)](https://thangs.com)"
    )
    await message.answer(text, parse_mode="Markdown")

# ---------------- ВЕБ-СЕРВЕР ДЛЯ RENDER (KEEP-ALIVE) ----------------

async def handle_ping(request):
    return web.Response(text="Dryguny Bot is Running!")

async def main():
    # Налаштовуємо сервер, щоб Render не вимикав бота
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Використовуємо PORT, який надає Render автоматично
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"✅ Web server is live on port {port}")

    # Запуск бота (видаляємо старі оновлення і стартуємо)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ---------------- ЗАПУСК ----------------

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинений")
