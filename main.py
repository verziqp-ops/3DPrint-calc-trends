import asyncio
import os
import zipfile
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# Твій токен
API_TOKEN = '8594286835:AAFuEBZnWbTlkRpmMJ0xf03V7tWgEMGmYjQ'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def parse_3mf(file_path):
    """Витягуємо вагу прямо з тегів Bambu Studio всередині .3mf"""
    try:
        with zipfile.ZipFile(file_path, 'r') as archive:
            for name in archive.namelist():
                if 'Metadata/model_settings.config' in name or '.gcode' in name:
                    with archive.open(name) as f:
                        data = f.read().decode('utf-8', errors='ignore')
                        # Шукаємо вагу
                        weight_match = re.search(r'filament_weight\\":\\"([\d\.]+)', data)
                        if not weight_match:
                            weight_match = re.search(r'total filament weight \[g\]\s*:\s*([\d\.]+)', data)
                        return weight_match.group(1) if weight_match else "0"
    except: return "0"
    return "0"

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = [[types.InlineKeyboardButton(text="💎 Калькулятор Dryguny", url="https://verziqp-ops.github.io/3DPrint-calc-trends/?v=3")]]
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("🛠 Бот Dryguny активований 24/7!\n\nСкидай .3mf файл, я скажу вагу, або відкривай калькулятор:", reply_markup=reply_markup)

@dp.message(F.document)
async def handle_doc(message: types.Message):
    if message.document.file_name.lower().endswith('.3mf'):
        wait_msg = await message.answer("📡 Аналізую проєкт...")
        file_info = await bot.get_file(message.document.file_id)
        file_path = "temp.3mf"
        await bot.download_file(file_info.file_path, file_path)
        
        weight = parse_3mf(file_path)
        os.remove(file_path)
        
        await wait_msg.edit_text(f"⚖️ Вага для друку: **{weight}г**\n\nВпиши це число в калькулятор!")
    else:
        await message.answer("Я розумію тільки файли .3mf")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())