from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle
import asyncio

bot = Bot("YOUR BOT TOKEN HERE")

dp = Dispatcher()

"""
this is an inline query search which 
in real time auto completes user's input
for further info go here:
https://core.telegram.org/bots/api#inline-mode
"""

items = {
    "ruben": "boss kofemanii",
    "lexa": "boss kfc",
    "lev": "tigr",
    "misha": "winner mindset"
}

@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip().lower()
    results = []

    for item_name, item_description in items.items():
        if query in item_name:
            result = InlineQueryResultArticle(
                id=item_name,  
                title=item_name.capitalize(),
                input_message_content=InputTextMessageContent(message_text=item_description), 
                description=item_description,
            )
            results.append(result)

    await bot.answer_inline_query(inline_query.id, results, cache_time=1)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
