import os
import asyncio
import logging
import urllib.parse
import aiohttp
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# --- КОНФІГУРАЦІЯ ШІ ---
GOOGLE_API_KEY = "AIzaSyAkmMTOz4uDgr8hKGTFkNYV2UtXL9GV7qk"
genai.configure(api_key=GOOGLE_API_KEY)

# Автоматичний вибір доступної моделі
def get_model():
    for model_name in ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']:
        try:
            m = genai.GenerativeModel(model_name)
            # Перевірка на працездатність
            return m
        except:
            continue
    return genai.GenerativeModel('gemini-1.5-flash')

ai_model = get_model()

AI_INSTRUCTION = (
    "Ти — Dryguny AI, асистент бренду Dryguny. Твій власник — Макс. "
    "Ти експерт у 3D-друці, Bambu Lab та Blender. Відповідай коротко та з емодзі."
)

# --- КОНФІГУРАЦІЯ БОТА ---
TOKEN = "8594286835:AAHiMtMF9goo8achqLiBvEW8cR858-ZpMaU" 
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("🚀 **Dryguny AI Hub v3.3**\nКоманда `/help [питання]` для зв'язку з ШІ.", parse_mode="Markdown")

@dp.message(Command("help"))
async def ai_help_handler(message: types.Message):
    user_query = message.text.replace("/help", "").strip()
    if not user_query:
        await message.answer("🆘 Напиши питання!")
        return

    status_msg = await message.answer("🧠 *Dryguny AI аналізує...*")
    try:
        # Виправлений виклик генерації
        response = await asyncio.to_thread(ai_model.generate_content, f"{AI_INSTRUCTION}\n\nПитання: {user_query}")
        
        await bot.edit_message_text(
            text=f"🤖 **Відповідь:**\n\n{response.text}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await bot.edit_message_text(text=f"⚠️ Помилка моделі. Спробуй пізніше.", chat_id=message.chat.id, message_id=status_msg.message_id)

@dp.message(Command("find"))
async def find_stl_handler(message: types.Message):
    query = message.text.replace("/find", "").strip()
    if not query: return await message.answer("❌ Що шукаємо?")
    q = urllib.parse.quote(query)
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💎 MakerWorld", url=f"https://makerworld.com/en/models/search?keyword={q}")]
    ])
    await message.answer(f"🔍 Пошук: {query}", reply_markup=markup)

@dp.message(Command("filament"))
async def filament_handler(message: types.Message):
    try:
        args = message.text.split()
        material = args[1]
        prices = args[2].split("-")
        url = f"https://prom.ua/ua/search?search_term={material}+filament&price_local__gte={prices[0]}&price_local__lte={prices[1]}"
        await message.answer(f"🧵 [Результати на Prom.ua]({url})", parse_mode="Markdown")
    except:
        await message.answer("❌ Формат: `/filament pla 400-800`")

async def handle_ping(request): return web.Response(text="OK")

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
