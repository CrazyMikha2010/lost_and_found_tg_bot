from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle
import asyncio
from config_reader import config

bot = Bot(token=config.bot_token.get_secret_value())

dp = Dispatcher()

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
