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

# ВИПРАВЛЕНО: Використовуємо gemini-pro для стабільності, якщо flash видає 404
try:
    ai_model = genai.GenerativeModel(model_name="gemini-pro")
except:
    ai_model = genai.GenerativeModel(model_name="models/gemini-pro")

# Інструкція для ШІ
AI_INSTRUCTION = (
    "Ти — Dryguny AI, офіційний асистент бренду Dryguny. Твій власник — Макс. "
    "Ти експерт у 3D-друці, техніці Bambu Lab, моделюванні в Blender та Fusion 360. "
    "Відповідай коротко, технічно грамотно, з емодзі та гумором. "
    "Якщо Макс питає про помилки друку — давай чіткі кроки виправлення."
)

# --- КОНФІГУРАЦІЯ БОТА ---
# Використовуємо твій останній токен
TOKEN = "8594286835:AAFPqy4iOs66tTN1VfL6EVucUQMOR6uFUx8" 
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ОБРОБНИКИ КОМАНД ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 **Dryguny AI Hub активований!**\n\n"
        "Твій персональний ШІ-помічник готовий.\n\n"
        "📜 **Команди:**\n"
        "🤖 `/help [питання]` — запитати у ШІ (Gemini)\n"
        "🔍 `/find [модель]` — знайти STL файли\n"
        "🧵 `/filament [тип] [ціна-ціна]` — пошук пластику\n"
        "🔥 `/trends` — свіжий хайп для друку",
        parse_mode="Markdown"
    )

# 1. РОЗУМНА ДОПОМОГА (GEMINI AI)
@dp.message(Command("help"))
async def ai_help_handler(message: types.Message):
    user_query = message.text.replace("/help", "").strip()
    
    if not user_query:
        await message.answer("🆘 Опиши свою проблему після команди, наприклад:\n`/help відклеюється перший слой`", parse_mode="Markdown")
        return

    status_msg = await message.answer("🧠 *Dryguny AI аналізує проблему...*", parse_mode="Markdown")

    try:
        # 2. Запускаємо генерацію
        full_prompt = f"{AI_INSTRUCTION}\n\nПитання: {user_query}"
        
        # Використовуємо простіший метод виклику для уникнення помилок версій
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: ai_model.generate_content(full_prompt))
        
        # Перевіряємо, чи є відповідь
        if response.text:
            await bot.edit_message_text(
                text=f"🤖 **Порада від Dryguny AI:**\n\n{response.text}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode="Markdown"
            )
        else:
            await bot.edit_message_text(text="⚠️ ШІ не зміг згенерувати відповідь. Спробуй інше питання.", chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        logging.error(f"AI Error: {e}")
        await bot.edit_message_text(
            text=f"⚠️ Помилка ШІ: {str(e)}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

# 2. ПОШУК STL ФАЙЛІВ
@dp.message(Command("find"))
async def find_stl_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query:
        await message.answer("❌ Напиши назву моделі: `/find dragon`")
        return

    q = urllib.parse.quote(query)
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💎 MakerWorld", url=f"https://makerworld.com/en/models/search?keyword={q}")],
        [types.InlineKeyboardButton(text="🧩 Printables", url=f"https://www.printables.com/search/models?q={q}")],
        [types.InlineKeyboardButton(text="💰 Cults3D", url=f"https://cults3d.com/en/search?q={q}")]
    ])
    await message.answer(f"🔍 **Шукаю моделі для: {query}**", reply_markup=markup, parse_mode="Markdown")

# 3. ПОШУК ФІЛАМЕНТУ
@dp.message(Command("filament"))
async def filament_handler(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.answer("❌ Формат: `/filament pla 400-800`")
            return

        material, p_range = args[1].lower(), args[2].split("-")
        min_p, max_p = p_range[0], p_range[1]
        
        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={min_p}&price_local__lte={max_p}"
        await message.answer(f"🧵 Пошук {material.upper()} ({min_p}-{max_p} грн):\n[Відкрити результати на Prom.ua]({url})", parse_mode="Markdown")
    except:
        await message.answer("⚠️ Помилка формату ціни.")

# 4. ТРЕНДИ
@dp.message(Command("trends"))
async def trends_handler(message: types.Message):
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔥 MakerWorld Trends", url="https://makerworld.com/uk")],
        [types.InlineKeyboardButton(text="🎬 TikTok 3D Ideas", url="https://www.tiktok.com/search/video?q=3d%20printing%20ideas")]
    ])
    await message.answer("🚀 **Свіжі ідеї для Dryguny:**", reply_markup=markup)

# --- WEB SERVER ---

async def handle_ping(request):
    return web.Response(text="Dryguny AI is Running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ГОЛОВНИЙ ЗАПУСК ---

async def main():
    await start_webserver()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Dryguny AI Bot запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Зупинка")
        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={min_p}&price_local__lte={max_p}"
        await message.answer(f"🧵 Пошук {material.upper()} ({min_p}-{max_p} грн):\n[Відкрити результати на Prom.ua]({url})", parse_mode="Markdown")
    except:
        await message.answer("⚠️ Помилка формату ціни.")

# 4. ТРЕНДИ
@dp.message(Command("trends"))
async def trends_handler(message: types.Message):
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔥 MakerWorld Trends", url="https://makerworld.com/uk")],
        [types.InlineKeyboardButton(text="🎬 TikTok 3D Ideas", url="https://www.tiktok.com/search/video?q=3d%20printing%20ideas")]
    ])
    await message.answer("🚀 **Свіжі ідеї для Dryguny:**", reply_markup=markup)

# --- WEB SERVER (Для Render) ---

async def handle_ping(request):
    return web.Response(text="Dryguny AI is Running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ГОЛОВНИЙ ЗАПУСК ---

async def main():
    await start_webserver()
    # Очищуємо старі апдейти, щоб уникнути конфліктів (Conflict Error)
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Dryguny AI Bot запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Зупинка")


