import os
import asyncio
import logging
import urllib.parse
import aiohttp
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# Налаштування логів
logging.basicConfig(level=logging.INFO)

# --- КОНФІГУРАЦІЯ ШІ ---
GOOGLE_API_KEY = "AIzaSyAkmMTOz4uDgr8hKGTFkNYV2UtXL9GV7qk"
genai.configure(api_key=GOOGLE_API_KEY)

# Використовуємо стабільну модель
try:
    ai_model = genai.GenerativeModel(model_name="gemini-pro")
except:
    ai_model = genai.GenerativeModel(model_name="models/gemini-pro")

# Інструкція для ШІ
AI_INSTRUCTION = (
    "Ти — Dryguny AI, офіційний асистент бренду Dryguny. Твій власник — Макс. "
    "Ти експерт у 3D-друці, техніці Bambu Lab, моделюванні в Blender та Fusion 360. "
    "Відповідай коротко, технічно грамотно, з емодзі та гумором."
)

# --- КОНФІГУРАЦІЯ БОТА ---
TOKEN = "8594286835:AAHiMtMF9goo8achqLiBvEW8cR858-ZpMaU" 
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ОБРОБНИКИ КОМАНД ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 **Dryguny AI Hub v3.2**\n\n"
        "🤖 `/help [питання]` — запитати у ШІ\n"
        "🔍 `/find [модель]` — знайти STL\n"
        "🧵 `/filament [тип] [мін-макс]` — пошук пластику\n"
        "🔥 `/trends` — ідеї для друку",
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def ai_help_handler(message: types.Message):
    user_query = message.text.replace("/help", "").strip()
    if not user_query:
        await message.answer("🆘 Напиши питання після команди!")
        return

    status_msg = await message.answer("🧠 *Dryguny AI думає...*", parse_mode="Markdown")
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: ai_model.generate_content(f"{AI_INSTRUCTION}\n\nПитання: {user_query}"))
        
        await bot.edit_message_text(
            text=f"🤖 **Відповідь:**\n\n{response.text}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )
    except Exception as e:
        await bot.edit_message_text(text=f"⚠️ Помилка: {str(e)}", chat_id=message.chat.id, message_id=status_msg.message_id)

@dp.message(Command("find"))
async def find_stl_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query:
        await message.answer("❌ Напиши назву моделі!")
        return
    q = urllib.parse.quote(query)
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💎 MakerWorld", url=f"https://makerworld.com/en/models/search?keyword={q}")],
        [types.InlineKeyboardButton(text="🧩 Printables", url=f"https://www.printables.com/search/models?q={q}")]
    ])
    await message.answer(f"🔍 Шукаю: {query}", reply_markup=markup)

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.answer("❌ Формат: `/filament pla 400-800`")
            return
        material = args[1].lower()
        prices = args[2].split("-")
        min_p, max_p = prices[0], prices[1]
        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={min_p}&price_local__lte={max_p}"
        # ТУТ БУЛА ПОМИЛКА З ВІДСТУПАМИ
        await message.answer(f"🧵 Пошук {material.upper()} ({min_p}-{max_p} грн):\n[Результати на Prom.ua]({url})", parse_mode="Markdown")
    except Exception as e:
        await message.answer("⚠️ Помилка у форматі ціни.")

@dp.message(Command("trends"))
async def trends_handler(message: types.Message):
    await message.answer("🚀 **Тренди:**\n1. [MakerWorld](https://makerworld.com/uk)\n2. [TikTok Ideas](https://www.tiktok.com/search/video?q=3d%20printing%20ideas)", parse_mode="Markdown")

# --- СЕРВЕР ТА ЗАПУСК ---

async def handle_ping(request):
    return web.Response(text="Running")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()
    
    # Цей рядок вбиває старі сесії, щоб не було Conflict Error
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
