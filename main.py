import os
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup  # Додали цей імпорт
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
        "Я допоможу тобі з розрахунками та пошуком.\n"
        "• /trends — що зараз модно\n"
        "• /filament [тип] [ціна-ціна] — пошук пластику\n"
        "Наприклад: `/filament pla 400-800`",
        parse_mode="Markdown"
    )

@dp.message(Command("trends"))
async def trends_handler(message: types.Message):
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔥 MakerWorld (Bambu Lab)", url="https://makerworld.com/uk")],
        [types.InlineKeyboardButton(text="🧩 Printables Trending", url="https://www.printables.com/model?period=week&sort=trending")],
        [types.InlineKeyboardButton(text="🎬 TikTok (3D Printing)", url="https://www.tiktok.com/search/video?q=3d%20printing%20ideas")],
        [types.InlineKeyboardButton(text="📦 Thingiverse Popular", url="https://www.thingiverse.com/?page=1&sort=popular&posted_after=now-7d")]
    ])
    await message.answer("🚀 **Пошук трендових моделей:**", reply_markup=markup)

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.answer("❌ Формат: `/filament pla 400-700`", parse_mode="Markdown")
            return

        material = args[1].lower()
        price_range = args[2].split("-")
        min_price = int(price_range[0])
        max_price = int(price_range[1])

        await message.answer(f"🔍 Шукаю {material} від {min_price} до {max_price} грн на Prom...")

        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

        # --- ПОШУК НА PROM (через HTML, бо API закрите) ---
        prom_url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={min_price}&price_local__lte={max_price}"
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(prom_url) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    # Шукаємо картки товарів
                    items = soup.find_all("div", {"data-qaid": "product_block"})[:7]
                    
                    for item in items:
                        name_tag = item.find("span", {"data-qaid": "product_name"})
                        price_tag = item.find("span", {"data-qaid": "product_price"})
                        link_tag = item.find("a", {"data-qaid": "product_link"})
                        
                        if name_tag and price_tag and link_tag:
                            name = name_tag.text.strip()
                            # Очищуємо ціну від зайвих символів
                            price_val = "".join(filter(str.isdigit, price_tag.get("data-qaprice") or price_tag.text))
                            link = "https://prom.ua" + link_tag["href"]
                            
                            if price_val:
                                results.append(f"📦 {name}\n💰 **{price_val} грн**\n🔗 [Купити на Prom]({link})")

        if not results:
            await message.answer("❌ Нічого не знайдено. Спробуй змінити діапазон цін.")
        else:
            reply = f"🧵 **Знайдено для Dryguny:**\n\n" + "\n\n".join(results)
            await message.answer(reply, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Помилка: {e}")
        await message.answer("⚠️ Помилка пошуку. Перевір формат ціни (наприклад 400-800).")

@dp.message()
async def echo_handler(message: types.Message):
    await message.answer("Я отримав повідомлення! Працюю...")

# --- СЕРВЕР ТА ЗАПУСК ---
async def handle_ping(request):
    return web.Response(text="Dryguny Bot is Running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_webserver()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
