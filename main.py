import os
import asyncio
import logging
import urllib.parse
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# 1. НАЛАШТУВАННЯ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Твій ID (дізнайся в @userinfobot)
ADMIN_ID = 6259271140  

TOKEN = os.environ.get("BOT_TOKEN", "8594286835:AAErm6y6PHa6Pf1ZjcAaTg-osw-yFBUFbhc")

bot = Bot(token=TOKEN)
# Додаємо сховище для станів (ланцюжка діалогу)
dp = Dispatcher(storage=MemoryStorage())

# Стан для додавання товару
class ShopForm(StatesGroup):
    choosing_category = State()
    confirming = State()

# ---------------- КОМАНДА /addtoshop ----------------

@dp.message(Command("addtoshop"))
async def add_to_shop_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Тільки Макс може додавати товари.")

    args = message.text.split()
    if len(args) < 2:
        return await message.answer("❌ Формат: `/addtoshop [посилання]`", parse_mode="Markdown")
    
    url = args[1]
    await state.update_data(product_url=url)

    # Клавіатура з категоріями (твоя правка)
    kb = [
        [types.KeyboardButton(text="🗿 Статуетки"), types.KeyboardButton(text="👾 Фігурки")],
        [types.KeyboardButton(text="🔑 Брелоки"), types.KeyboardButton(text="🏠 Для дому")]
    ]
    markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

    await message.answer("📁 **Обери категорію для моделі:**", reply_markup=markup, parse_mode="Markdown")
    await state.set_state(ShopForm.choosing_category)

@dp.message(ShopForm.choosing_category)
async def category_chosen(message: types.Message, state: FSMContext):
    category = message.text
    data = await state.get_data()
    url = data['product_url']

    # Імітація роботи ШІ (тут можна підключити Gemini API)
    # Поки що просто робимо "привабливий опис" на основі посилання
    name_from_url = url.split('/')[-1].replace('-', ' ').title()
    ai_desc = (
        f"🔥 **Новинка: {name_from_url}!**\n\n"
        f"Ця модель у категорії {category} стане ідеальним доповненням твого робочого місця. "
        f"Висока деталізація та преміальна якість друку. \n\n"
        f"📍 Посилання: {url}"
    )

    await state.update_data(category=category, desc=ai_desc, name=name_from_url)

    # Показуємо фінальний результат перед публікацією
    confirm_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ ПІДТВЕРДИТИ", callback_data="conf_ok")],
        [types.InlineKeyboardButton(text="📝 ЗМІНИТИ", callback_data="conf_edit")],
        [types.InlineKeyboardButton(text="❌ СКАСУВАТИ", callback_data="conf_cancel")]
    ])

    await message.answer(
        f"🎨 **Ось так це буде в магазині:**\n\n{ai_desc}\n\n*Картинка підтягнеться автоматично*",
        reply_markup=confirm_kb,
        parse_mode="Markdown"
    )
    await state.set_state(ShopForm.confirming)

@dp.callback_query(F.data.startswith("conf_"))
async def process_confirm(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]

    if action == "ok":
        data = await state.get_data()
        # ТУТ ЛОГІКА ЗАПИСУ В БАЗУ ДАНИХ (Firebase/Supabase)
        logger.info(f"Додано в магазин: {data['name']}")
        await callback.message.edit_text(f"✅ **Успішно!** Товар '{data['name']}' додано у вкладку {data['category']}.")
    
    elif action == "edit":
        await callback.message.answer("Введи новий опис вручну:")
        # Тут можна додати стан для редагування
    
    else:
        await callback.message.edit_text("❌ Скасовано.")
    
    await state.clear()

# ---------------- ТВОЇ СТАРІ КОМАНДИ (БЕЗ ЗМІН) ----------------

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🚀 **Вітаємо у Dryguny 3D Hub!**\n\n"
        "🔍 `/find [назва]` — пошук STL\n"
        "🛍 `/addtoshop [url]` — додати товар (Адмін)",
        parse_mode="Markdown"
    )

# ... (решта твоїх команд: find, idea, filament, viral, trend залишаються як були)

# ---------------- ВЕБ-СЕРВЕР ТА ЗАПУСК ----------------

async def handle_ping(request):
    return web.Response(text="Dryguny Bot is Running! 🚀")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
