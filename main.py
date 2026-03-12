import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# Налаштування логів
logging.basicConfig(level=logging.INFO)

# --- КОНФІГУРАЦІЯ ---
TOKEN = "8594286835:AAFuEBZnWbTlkRpmMJ0xf03V7tWgEMGmYjQ" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ОБРОБНИКИ ПОВІДОМЛЕНЬ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🛠 **Бот Dryguny активований 24/7!**\n\n"
        "Я допоможу тобі з розрахунками для 3D-друку.\n"
        "Використовуй команду /trends щоб знайти ідеї для друку.",
        parse_mode="Markdown"
    )

# ЦЕЙ БЛОК МАЄ БУТИ ТУТ (Вище за ехо-handler)
@dp.message(Command("trends"))
async def trends_handler(message: types.Message):
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔥 MakerWorld (Bambu Lab)", url="https://makerworld.com/uk")],
        [types.InlineKeyboardButton(text="🧩 Printables Trending", url="https://www.printables.com/model?period=week&sort=trending")],
        [types.InlineKeyboardButton(text="🎬 TikTok (3D Printing)", url="https://www.tiktok.com/search/video?q=3d%20printing%20ideas")],
        [types.InlineKeyboardButton(text="📦 Thingiverse Popular", url="https://www.thingiverse.com/?page=1&sort=popular&posted_after=now-7d")]
    ])
    
    await message.answer(
        "🚀 **Пошук трендових моделей для Dryguny:**\n\n"
        "Обирай платформу, щоб побачити, що зараз популярно:",
        reply_markup=markup
    )

import aiohttp
from bs4 import BeautifulSoup

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):
    try:
        args = message.text.split()

        if len(args) < 3:
            await message.answer("Приклад:\n/filament pla 400-500")
            return

        material = args[1].lower()
        price_range = args[2].split("-")

        min_price = int(price_range[0])
        max_price = int(price_range[1])

        results = []

        shops = [
            f"https://prom.ua/ua/search?search_term={material}+filament",
            f"https://rozetka.com.ua/ua/search/?text={material}%20filament"
        ]

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        async with aiohttp.ClientSession(headers=headers) as session:

            for shop in shops:
                async with session.get(shop) as resp:
                    html = await resp.text()

                    soup = BeautifulSoup(html, "html.parser")

                    products = soup.find_all("a", href=True)

                    for p in products[:30]:

                        text = p.get_text().lower()

                        if material in text:

                            price_text = ''.join(filter(str.isdigit, text))

                            if price_text:
                                price = int(price_text)

                                if min_price <= price <= max_price:
                                    link = p["href"]

                                    if not link.startswith("http"):
                                        link = shop + link

                                    results.append((text[:60], price, link))

                        if len(results) >= 5:
                            break

        if not results:
            await message.answer("❌ Нічого не знайдено в цьому діапазоні.")
            return

        reply = f"🧵 {material.upper()} {min_price}-{max_price} грн:\n\n"

        for i, r in enumerate(results, 1):
            reply += f"{i}️⃣ {r[0]}\n💰 {r[1]} грн\n🔗 {r[2]}\n\n"

        await message.answer(reply)

    except Exception as e:
        logging.error(e)
        await message.answer("⚠️ Помилка пошуку.")
        
# Ехо-handler завжди останній
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer("Я отримав твоє повідомлення! Працюю над функціоналом калькулятора...")

# --- СЕКЦІЯ WEB-SERVER (Для Render) ---

async def handle_ping(request):
    return web.Response(text="Dryguny Bot is Running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    logging.info(f"Веб-сервер запущено на порту {port}")
    await site.start()

# --- ГОЛОВНИЙ ЗАПУСК ---

async def main():
    await start_webserver()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот починає опитування (polling)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинений.")


