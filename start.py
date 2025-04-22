from config_reader import config
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Start text")

@dp.message(Command("help"))
async def cmd_start(message: types.Message):
    await message.answer("Help text")

@dp.message(Command("lost"))
async def cmd_lost(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Make order", callback_data="makeOrder")],
        [InlineKeyboardButton(text="View orders", callback_data="viewOrder")]])
    global tmp_q
    tmp_q = await message.answer("What do you want to do?", reply_markup=keyboard)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

@dp.callback_query(lambda c: c.data in ['makeOrder', 'viewOrder'])
async def process_cmd_lost(callback_query: types.CallbackQuery):
    button_clicked = callback_query.data
    if button_clicked == "makeOrder":
        await bot.answer_callback_query(callback_query.id)
        await bot.delete_message(chat_id=tmp_q.chat.id, message_id=tmp_q.message_id)
        await bot.send_message(chat_id=callback_query.message.chat.id, text="Fill out a form")

        global questions
        questions = ["Photo", "Category", "Short description", "Brand", "Color", "Where?", "Comments"] # grab user id as well
        global makingOrder
        makingOrder = True
        tmp_q = await bot.send_message(chat_id=callback_query.message.chat.id, text=questions[0])


            
    elif button_clicked == "viewOrder":
        ...
tmp_categories = []
if makingOrder:
    @dp.message()
    async def handle_message(message: types.Message):
        answer = message.text
        await bot.delete_message(chat_id=tmp_q.chat.id, message_id=tmp_q.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
