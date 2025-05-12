from config_reader import config
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class Bones: 
    dp = Dispatcher()

    def __init__(self):
        self.bot = Bot(token=config.bot_token.get_secret_value())
        self.makingOrder = False
        self.viewOrder = False
        self.tmp_q = False
        self.cur_q = 0
        self.questions = ["Photo", "Category", "Short description", "Brand", "Color", "Where", "Comments"] # grab user id as well
        self.tmp_categories = []

        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_lost, Command("lost"))
        self.dp.callback_query.register(self.process_cmd_lost, lambda c: c.data in ['makeOrder', 'viewOrder'])
        self.dp.message.register(self.handle_message)
        self.dp.message.register(self.get_photo)


    async def cmd_start(self, message: types.Message):
        await message.answer("Start text")

    async def cmd_help(self, message: types.Message):
        await message.answer("Help text")

    async def cmd_lost(self, message: types.Message):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Make order", callback_data="makeOrder")],
            [InlineKeyboardButton(text="View orders", callback_data="viewOrder")]])
        self.tmp_q = await message.answer("What do you want to do?", reply_markup=keyboard)
        await self.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    async def process_cmd_lost(self, callback_query: types.CallbackQuery):
        button_clicked = callback_query.data
        await self.bot.answer_callback_query(callback_query.id)
        if button_clicked == "makeOrder":
            await self.bot.delete_message(chat_id=self.tmp_q.chat.id, message_id=self.tmp_q.message_id)
            self.fill_form = await self.bot.send_message(chat_id=callback_query.message.chat.id, text="Fill out a form")

            self.tmp_q = await self.bot.send_message(chat_id=callback_query.message.chat.id, text=self.questions[0])
            self.makingOrder = True
                
        elif button_clicked == "viewOrder":
            self.viewOrder = True

    async def get_photo(self, message: types.Message):
        private_channel_id = '@lost_and_found_helper' 
        forwarded_message = await self.bot.forward_message(chat_id=private_channel_id, from_chat_id=message.chat.id, message_id=message.message_id)
        file_id = forwarded_message.photo[-1].file_id
        self.tmp_categories.append(file_id)
        await self.bot.delete_message(chat_id=self.tmp_q.chat.id, message_id=self.tmp_q.message_id)
        await self.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        self.cur_q += 1
        self.tmp_q = await self.bot.send_message(chat_id=message.chat.id, text=self.questions[self.cur_q])

    async def handle_message(self, message: types.Message):
        if self.makingOrder:
            if self.cur_q == 0: # photo
                await self.get_photo(message)
            elif self.cur_q == 10:
                await self.finish_makingOrder(message)
            else:
                answer = message.text
                self.tmp_categories.append(answer)
                await self.bot.delete_message(chat_id=self.tmp_q.chat.id, message_id=self.tmp_q.message_id)
                await self.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                self.tmp_q = await self.bot.send_message(chat_id=message.chat.id, text=self.questions[self.cur_q])
                
                if self.cur_q == 6:
                    self.cur_q = 9
            self.cur_q += 1
        elif self.viewOrder:
            ...

    async def finish_makingOrder(self, message: types.Message):
        self.makingOrder = False
        self.cur_q = 0
        answer = message.text
        await self.bot.delete_message(chat_id=self.tmp_q.chat.id, message_id=self.tmp_q.message_id)
        await self.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        self.tmp_categories.append(answer)
        await self.bot.delete_message(chat_id=self.fill_form.chat.id, message_id=self.fill_form.message_id)
        self.submit = False
        summ_t = str()
        for i in range(1, len(self.questions)):
            summ_t += f'{self.questions[i]}: {self.tmp_categories[i]}' + '\n'
        
        self.summ = await self.bot.send_photo(chat_id=self.fill_form.chat.id, photo=self.tmp_categories[0], caption=summ_t)
            


        

    # async def submit_order(self):
    #     summ_t = str()
    #     for i in range(1, len(self.questions)):
    #         summ_t += f'{self.questions[i]}: {self.tmp_categories[i]}' + '\n'
        
    #     self.summ = await self.bot.send_photo(chat_id=self.fill_form.chat.id, photo=self.tmp_categories[0], caption=summ_t)
        


    async def main(self):
        await self.dp.start_polling(self.bot)
    

if __name__ == "__main__":
    b = Bones()
    asyncio.run(b.main())


