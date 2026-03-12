import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Налаштування логів (щоб бачити помилки в Render Logs)
logging.basicConfig(level=logging.INFO)

# --- КОНФІГУРАЦІЯ ---
# Встав сюди свій токен, який ти отримав у @BotFather
TOKEN = "ТУТ_ТВІЙ_ТОКЕН_БОТА" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ОБРОБНИКИ ПОВІДОМЛЕНЬ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🛠 **Бот Dryguny активований 24/7!**\n\n"
        "Я допоможу тобі з розрахунками для 3D-друку.\n"
        "• Скидай .3mf файл для аналізу вагою\n"
        "• Або скористайся калькулятором нижче 👇",
        parse_mode="Markdown"
    )

# Відповідь на будь-яке інше повідомлення
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer("Я отримав твоє повідомлення! Працюю над функціоналом калькулятора...")

# --- СЕКЦІЯ WEB-SERVER (Для Cron-job та Render) ---

async def handle_ping(request):
    """Ця функція відповідає Cron-job, що бот живий"""
    return web.Response(text="Dryguny Bot is Running!")

async def start_webserver():
    """Запуск сервера на порту, який дає Render"""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматично призначає порт через змінну оточення PORT
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logging.info(f"Веб-сервер запущено на порту {port}")
    await site.start()

# --- ГОЛОВНИЙ ЗАПУСК ---

async def main():
    # 1. Запускаємо веб-сервер (будильник)
    await start_webserver()
    
    # 2. Видаляємо старі повідомлення, які прийшли поки бот був офлайн
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 3. Запускаємо слухання Telegram
    logging.info("Бот починає опитування (polling)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинений.")
