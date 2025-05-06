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

import sqlite3

from datetime import datetime

from config_reader import config

def init_db():
    conn = sqlite3.connect("found_items.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS found_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            file_id TEXT NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

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

@dp.message(lambda message: message.text == "/found")
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
    await state.update_data(last_bot_message=callback.message.message_id)

@dp.message(LostForm.photo)
async def receive_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Please send a valid photo.")
        return

    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔍 Search Category",
            switch_inline_query_current_chat=" "
        )]
    ])
    msg = await message.answer("Search for a category:", reply_markup=keyboard)
    await state.update_data(last_bot_message=msg.message_id)
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

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

async def show_summary(message: Message, data: dict, state: FSMContext):
    # Delete previous summary and buttons
    summary_msg_id = data.get('summary_message')
    buttons_msg_id = data.get('buttons_message')

    if summary_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=summary_msg_id)
        except Exception:
            pass

    if buttons_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=buttons_msg_id)
        except Exception:
            pass

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

    new_summary_msg = None
    if data.get("photo"):
        new_summary_msg = await message.answer_photo(photo=data["photo"], caption=summary, parse_mode=ParseMode.HTML)
    else:
        new_summary_msg = await message.answer(summary, parse_mode=ParseMode.HTML)

    new_buttons_msg = await message.answer("Is everything correct?", reply_markup=confirm_keyboard)

    await state.update_data(
        summary_message=new_summary_msg.message_id,
        buttons_message=new_buttons_msg.message_id
    )

@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def handle_edit(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("edit_", "")

    if action == "photo":
        msg = await callback.message.answer("📸 Please send a new photo.")
        await state.update_data(last_bot_message=msg.message_id)
        await state.set_state(EditingForm.photo)
    elif action == "category":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔍 Search Category",
                switch_inline_query_current_chat=" "
            )]
        ])
        msg = await callback.message.answer("Search for a category:", reply_markup=keyboard)
        await state.update_data(last_bot_message=msg.message_id)
        await state.set_state(EditingForm.category)
    elif action == "location":
        msg = await callback.message.answer("Where was it lost? (Type `-` to skip)")
        await state.update_data(last_bot_message=msg.message_id)
        await state.set_state(EditingForm.location)
    elif action == "comments":
        msg = await callback.message.answer("Add or edit your comments: (Type `-` to skip)")
        await state.update_data(last_bot_message=msg.message_id)
        await state.set_state(EditingForm.comments)

    data = await state.get_data()
    summary_msg_id = data.get('summary_message')
    buttons_msg_id = data.get('buttons_message')

    if summary_msg_id:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=summary_msg_id)
        except Exception:
            pass

    if buttons_msg_id:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=buttons_msg_id)
        except Exception:
            pass

    await callback.answer()

@dp.message(EditingForm.photo)
async def update_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Please send a valid photo.")
        return

    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

@dp.message(EditingForm.category, lambda m: m.text.startswith("SELECTED_CATEGORY:"))
async def update_category(message: Message, state: FSMContext):
    raw = message.text.replace("SELECTED_CATEGORY:", "").strip()
    category_name = CATEGORIES.get(raw, "Unknown")
    await state.update_data(category=category_name)
    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

@dp.message(EditingForm.location)
async def update_location(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await message.answer("Skipped updating location.")
    else:
        await state.update_data(location=message.text)

    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

@dp.message(EditingForm.comments)
async def update_comments(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await message.answer("Skipped updating comments.")
    else:
        await state.update_data(comments=message.text)

    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

@dp.callback_query(lambda c: c.data == "confirm_submit")
async def confirm_submission(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    summary = (
        f"✅ Your Form:\n"
        f"Category: {data.get('category', '-')}\n"
        f"Location: {data.get('location', '-')}\n"
        f"Comments: {data.get('comments', '-')}"
    )

    summary_for_lost = (
        f"Location: {data.get('location', '-')}\n"
        f"Comments: {data.get('comments', '-')}\n"
        f"Date: {datetime.now().date()}"
    )

    try:
        sent_msg = await bot.send_photo(chat_id="@lost_and_found_helper", photo=data["photo"], caption=summary_for_lost)
        submit_msg = await callback.message.answer("✅ Form submitted and photo saved to the channel.")
        await state.update_data(submit_message=submit_msg.message_id)

        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO found_items (file_id, category, date)
            VALUES (?, ?, ?)
        ''', (sent_msg.photo[-1].file_id, data.get("category", "Unknown"), datetime.now().date()))
        conn.commit()
        conn.close()

    except Exception as e:
        error_msg = await callback.message.answer("⚠️ Failed to forward photo to the channel.")
        await state.update_data(submit_message=error_msg.message_id)
        print(e)

    # Clean up all tracked messages
    for msg_key in ['summary_message', 'buttons_message', 'submit_message']:
        msg_id = data.get(msg_key)
        if msg_id:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except Exception:
                pass

    await state.clear()
    await callback.answer()

@dp.message(EditingForm.photo)
async def update_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Please send a valid photo.")
        return

    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

@dp.message(EditingForm.category, lambda m: m.text.startswith("SELECTED_CATEGORY:"))
async def update_category(message: Message, state: FSMContext):
    raw = message.text.replace("SELECTED_CATEGORY:", "").strip()
    category_name = CATEGORIES.get(raw, "Unknown")
    await state.update_data(category=category_name)
    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

@dp.message(EditingForm.location)
async def update_location(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await message.answer("Skipped updating location.")
    else:
        await state.update_data(location=message.text)

    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

@dp.message(EditingForm.comments)
async def update_comments(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await message.answer("Skipped updating comments.")
    else:
        await state.update_data(comments=message.text)

    data = await state.get_data()

    last_msg_id = data.get('last_bot_message')
    if last_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    await show_summary(message, data, state)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    asyncio.run(main())
