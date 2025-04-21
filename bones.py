from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = '8069679804:AAHZPe9ZFaSXf5_Hy19c3DISMD-kHV4Vunw'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message_handler(commands=['start'])
async def 