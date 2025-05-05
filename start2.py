# start.py is terrible, had to restart again
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio

from config_reader import config

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

class LostForm(StatesGroup):
    photo = State()
    category = State()
    location = State()
    comments = State()

class EditingForm(StatesGroup):
    photo = State()
    category = State()
    location = State()
    comments = State()

CATEGORIES = {
    "pants": "👖 Штаны",
    "jackets": "🧥 Куртки",
    "sweaters": "🧣 Кофты",
    "shoes": "👟 Обувь",
    "bags": "🎒 Сумки",
    "hats": "🎩 Головные уборы",
    "badges": "🎖️ Бейджики",
    "chargers_electronics": "🔌 Зарядки",
    "electronics_devices": "💻 Электроника",
    "accessories": "🕶️ Аксессуары",
    "sports_gear": "🎾 Спортинвентарь",
    "money_cards": "💰 Деньги и карты",
    "other": "📦 Другое"
}

CATEGORY_DESCRIPTIONS = {
    "pants": "джинсы / спортивные / шорты",
    "jackets": "",
    "sweaters": "толстовки / зипки / футболки",
    "shoes": "спортивная / неспортивная",
    "bags": "",
    "hats": "шапки / кепки",
    "badges": "",
    "chargers_electronics": "",
    "electronics_devices": "компьютеры / телефоны / наушники",
    "accessories": "очки, кольца, ювелирка и тд",
    "sports_gear": "мячи, ракетки, гантели и тд",
    "money_cards": "",
    "other": ""
}


@dp.message(lambda message: message.text == "/lost")
async def cmd_lost(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Make Order", callback_data="makeOrder")],
        [InlineKeyboardButton(text="View Orders", callback_data="viewOrder")]
    ])
    await message.answer("What do you want to do?", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "makeOrder")
async def start_make_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LostForm.photo)
    await callback.message.edit_text("📸 Please send a photo.")


@dp.message(LostForm.photo)
async def receive_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Please send a valid photo.")
        return

    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("Search for a category using @lexa_rubin_lev_miha_bot <category>")
    await state.set_state(LostForm.category)


@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip().lower()
    results = []

    for key, title in CATEGORIES.items():
        description = CATEGORY_DESCRIPTIONS.get(key, "")
        full_text = (title + " " + description).lower()
        if query in full_text:
            result = InlineQueryResultArticle(
                id=key,
                title=title,
                input_message_content=InputTextMessageContent(
                    message_text=f"SELECTED_CATEGORY:{key}"
                ),
                description=description
            )
            results.append(result)

    await bot.answer_inline_query(inline_query.id, results, cache_time=1)


@dp.message(LostForm.category, lambda m: m.text.startswith("SELECTED_CATEGORY:"))
async def handle_category_selection(message: Message, state: FSMContext):
    raw = message.text.replace("SELECTED_CATEGORY:", "").strip()
    category_name = CATEGORIES.get(raw, "Unknown")

    await state.update_data(category=category_name)
    data = await state.get_data()
    await show_summary(message, data)


async def show_summary(message: Message, data: dict):
    summary = (
        f"📄 <b>Review Your Form:</b>\n"
        f"<b>Category:</b> {data.get('category', '-')}\n"
        f"<b>Location:</b> {data.get('location', '-')}\n"
        f"<b>Comments:</b> {data.get('comments', '-')}"
    )

    confirm_buttons = [
        [InlineKeyboardButton(text="✅ Confirm & Submit", callback_data="confirm_submit")],
        [
            InlineKeyboardButton(
                text="📷 Edit Photo" if data.get("photo") else "📸 Add Photo",
                callback_data="edit_photo"
            ),
            InlineKeyboardButton(
                text="🏷️ Edit Category" if data.get("category") else "🔍 Add Category",
                callback_data="edit_category"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Edit Location" if data.get("location") else "📍 Add Location",
                callback_data="edit_location"
            ),
            InlineKeyboardButton(
                text="💬 Edit Comment" if data.get("comments") else "📝 Add Comment",
                callback_data="edit_comments"
            )
        ]
    ]

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=confirm_buttons)

    try:
        last_msg = await bot.get_messages(chat_id=message.chat.id, message_ids=message.message_id - 1)
        if last_msg.text and "Review Your Form" in last_msg.text:
            await last_msg.edit_text(summary, parse_mode=ParseMode.HTML)
            await message.delete()
            await message.answer("Is everything correct?", reply_markup=confirm_keyboard)
            return
    except Exception:
        pass

    if data.get("photo"):
        await message.answer_photo(photo=data["photo"], caption=summary, parse_mode=ParseMode.HTML)
    else:
        await message.answer(summary, parse_mode=ParseMode.HTML)
    await message.answer("Is everything correct?", reply_markup=confirm_keyboard)


@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def handle_edit(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("edit_", "")

    if action == "photo":
        await callback.message.answer("📸 Please send a new photo.")
        await state.set_state(EditingForm.photo)
    elif action == "category":
        await callback.message.answer("Search for a category using @your_bot_username <category>")
        await state.set_state(EditingForm.category)
    elif action == "location":
        await callback.message.answer("Where was it lost? (Type `-` to skip)")
        await state.set_state(EditingForm.location)
    elif action == "comments":
        await callback.message.answer("Add or edit your comments: (Type `-` to skip)")
        await state.set_state(EditingForm.comments)

    await callback.answer()



@dp.message(EditingForm.photo)
async def update_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Please send a valid photo.")
        return

    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()
    await show_summary(message, data)

@dp.message(EditingForm.category, lambda m: m.text.startswith("SELECTED_CATEGORY:"))
async def update_category(message: Message, state: FSMContext):
    raw = message.text.replace("SELECTED_CATEGORY:", "").strip()
    category_name = CATEGORIES.get(raw, "Unknown")
    await state.update_data(category=category_name)
    data = await state.get_data()
    await show_summary(message, data)

@dp.message(EditingForm.location)
async def update_location(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await message.answer("Skipped updating location.")
    else:
        await state.update_data(location=message.text)

    data = await state.get_data()
    await show_summary(message, data)

@dp.message(EditingForm.comments)
async def update_comments(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await message.answer("Skipped updating comments.")
    else:
        await state.update_data(comments=message.text)

    data = await state.get_data()
    await show_summary(message, data)


@dp.callback_query(lambda c: c.data == "confirm_submit")
async def confirm_submission(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    summary = (
        f"✅ Your Form:\n"
        f"Category: {data.get('category', '-')}\n"
        f"Location: {data.get('location', '-')}\n"
        f"Comments: {data.get('comments', '-')}"
    )

    try:
        await bot.send_photo(chat_id="@lost_and_found_helper", photo=data["photo"], caption=summary)
        await callback.message.answer("✅ Form submitted and photo saved to the channel!")
    except Exception as e:
        await callback.message.answer("⚠️ Failed to forward photo to the channel.")
        print(e)

    await state.clear()
    await callback.answer()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
