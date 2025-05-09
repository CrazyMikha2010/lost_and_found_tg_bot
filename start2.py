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

from datetime import datetime, timedelta

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

class FilterForm(StatesGroup):
    category = State()
    days = State()

class SearchState(StatesGroup): 
    viewing = State()

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

def init_db():
    conn = sqlite3.connect("found_items.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS found_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            message_id TEXT NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            PRIMARY KEY (user_id, category)
        )
    ''')

    conn.commit()
    conn.close()

@dp.callback_query(lambda c: c.data.startswith("notif_delete_"))
async def handle_notification_delete(callback: CallbackQuery):
    msg_id = int(callback.data.split("_")[-1])
    
    try:
        await bot.delete_message(callback.message.chat.id, msg_id)
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting notification: {e}")
    
    await callback.answer("Notification deleted")

async def delete_notification(chat_id, message_id):
    await asyncio.sleep(30)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

#################################################################
##################  NOTIFICATIONS   #############################
#################################################################

class NotificationForm(StatesGroup):
    action = State()
    subscribe = State()
    unsubscribe = State()

@dp.message(lambda message: message.text == "/notification")
async def cmd_notification(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Subscribe", callback_data="notify_subscribe")],
        [InlineKeyboardButton(text="🔕 Unsubscribe", callback_data="notify_unsubscribe")]
    ])
    await message.answer("What would you like to do?", reply_markup=keyboard)
    await state.set_state(NotificationForm.action)

@dp.callback_query(lambda c: c.data in ["notify_subscribe", "notify_unsubscribe"])
async def handle_notification_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "subscribe":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔍 Search Category",
                switch_inline_query_current_chat="NOTIFY_SUBSCRIBE: "
            )]
        ])
        await callback.message.edit_text("Search for a category to subscribe:")
        await callback.message.answer("Search for a category:", reply_markup=keyboard)
        await state.set_state(NotificationForm.subscribe)
    else:
        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT category FROM user_subscriptions
            WHERE user_id = ?
        ''', (callback.from_user.id,))
        
        subscriptions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not subscriptions:
            await callback.message.edit_text("You have no active subscriptions.")
            await state.clear()
            return
        
        buttons = []
        for i in range(0, len(subscriptions), 2):
            row = subscriptions[i:i+2]
            buttons.append([
                InlineKeyboardButton(
                    text=f"❌ {CATEGORIES[cat]}",
                    callback_data=f"unsub_{cat}"
                ) for cat in row
            ])
        
        buttons.append([
            InlineKeyboardButton(
                text="✅ Finish", 
                callback_data="unsub_finish"
            )
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text("Tap categories to unsubscribe:", reply_markup=keyboard)
        await state.set_state(NotificationForm.unsubscribe)

@dp.inline_query(lambda q: q.query.startswith("NOTIFY_SUBSCRIBE:"))
async def inline_subscription_query(inline_query: InlineQuery):
    query = inline_query.query.replace("NOTIFY_SUBSCRIBE:", "").strip().lower()
    results = []
    
    for key, title in CATEGORIES.items():
        if query in title.lower() or query in key.lower():
            description = CATEGORY_DESCRIPTIONS.get(key, "")
            results.append(InlineQueryResultArticle(
                id=key,
                title=title,
                input_message_content=InputTextMessageContent(
                    message_text=f"SELECTED_SUB:{key}"
                ),
                description=description
            ))
    
    await bot.answer_inline_query(inline_query.id, results, cache_time=1)

@dp.message(NotificationForm.subscribe, lambda m: m.text.startswith("SELECTED_SUB:"))
async def handle_subscription_selection(message: Message, state: FSMContext):
    raw = message.text.replace("SELECTED_SUB:", "").strip()
    category = CATEGORIES.get(raw, None)
    
    if not category:
        await message.answer("Invalid category selected")
        return
    
    user_id = message.from_user.id
    
    try:
        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO user_subscriptions (user_id, category)
            VALUES (?, ?)
        ''', (user_id, raw))
        conn.commit()
        conn.close()
        
        await message.answer(f"✅ Subscribed to {category} notifications!")
    except Exception as e:
        await message.answer("❌ Failed to subscribe")
        print(f"Subscription error: {e}")
    
    await state.clear()


@dp.callback_query(lambda c: c.data.startswith("unsub_"))
async def handle_unsubscribe(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_", 1)[1]
    
    if data == "finish":
        await callback.message.delete()
        await callback.message.answer("✅ Subscription settings updated")
        await state.clear()
        return
    
    category = data
    user_id = callback.from_user.id
    
    try:
        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM user_subscriptions
            WHERE user_id = ? AND category = ?
        ''', (user_id, category))
        conn.commit()
        conn.close()
        
        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT category FROM user_subscriptions
            WHERE user_id = ?
        ''', (user_id,))
        
        subscriptions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        buttons = []
        for i in range(0, len(subscriptions), 2):
            row = subscriptions[i:i+2]
            buttons.append([
                InlineKeyboardButton(
                    text=f"❌ {CATEGORIES[cat]}",
                    callback_data=f"unsub_{cat}"
                ) for cat in row
            ])
        
        buttons.append([
            InlineKeyboardButton(
                text="✅ Finish", 
                callback_data="unsub_finish"
            )
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        
    except Exception as e:
        await callback.answer("Error updating subscription")
        print(f"Unsubscription error: {e}")

#################################################################
##################  NOTIFICATIONS   #############################
#################################################################

def get_category_item_count(category_key):
    try:
        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM found_items WHERE category = ?
        ''', (category_key,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"Error getting category count: {e}")
        return 0


def get_message_ids_by_category_and_days(category, max_days_back):
    try:
        cutoff_date = (datetime.now() - timedelta(days=int(max_days_back))).date()
        
        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT message_id 
            FROM found_items
            WHERE category = ?
              AND DATE(date) >= DATE(?)
            ORDER BY date DESC
        ''', (category, str(cutoff_date)))
        
        file_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return file_ids
        
    except Exception as e:
        print(f"Error fetching filtered items: {e}")
        return []


@dp.message(lambda message: message.text == "/lost")
async def cmd_filter(message: Message, state: FSMContext):
    msg = await message.answer("🔍 Which category would you like to see?")
    await state.update_data(last_bot_message=msg.message_id)
    await state.set_state(FilterForm.category)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔍 Search Category",
            switch_inline_query_current_chat=" "
        )]
    ])
    await message.answer("Search for a category:", reply_markup=keyboard)

@dp.message(FilterForm.category, lambda m: m.text.startswith("FILTER_CATEGORY:"))
async def handle_filter_category(message: Message, state: FSMContext):
    raw = message.text.replace("FILTER_CATEGORY:", "").strip()
    await state.update_data(filter_category=raw)
    
    data = await state.get_data()
    for msg_key in ['category_question', 'search_prompt_message']:
        msg_id = data.get(msg_key)
        if msg_id:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except Exception:
                pass
    
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass
    
    days_msg = await message.answer("📅 How many days back would you like to search?")
    await state.update_data(days_message=days_msg.message_id)
    await state.set_state(FilterForm.days)

@dp.message(FilterForm.days)
async def handle_filter_days(message: Message, state: FSMContext):
    days = message.text.strip()
    data = await state.get_data()

    days_msg_id = data.get('days_message')
    if days_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=days_msg_id)
        except Exception:
            pass
    
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    category_key = data.get('filter_category', 'Unknown') 
    message_ids = get_message_ids_by_category_and_days(category_key, days)

    if not message_ids:
        await message.answer(f"No items found in this category for the last {days} days.")
        await state.clear()
        return

    sent_messages = []
    
    for msg_id in message_ids:
        try:
            sent_msg = await bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id="@lost_and_found_helper",
                message_id=msg_id
            )
            sent_messages.append(sent_msg.message_id)
        except Exception as e:
            print(f"Error sending message {msg_id}: {e}")

    hide_orders_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Hide Orders", callback_data="hide_orders")]
    ])
    
    hide_msg = await message.answer("Click below to hide these orders:", reply_markup=hide_orders_button)
    
    await state.update_data(
        sent_messages=sent_messages,
        hide_button_message=hide_msg.message_id
    )
    await state.set_state(SearchState.viewing)

@dp.callback_query(lambda c: c.data == "hide_orders")
async def handle_hide_orders(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    result_ids = data.get('sent_messages', [])
    for msg_id in result_ids:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"Error deleting message {msg_id}: {e}")

    hide_msg_id = data.get('hide_button_message')
    if hide_msg_id:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=hide_msg_id)
        except Exception as e:
            print(f"Error deleting hide button: {e}")
    
    await state.clear()
    await callback.answer("All messages hidden")

@dp.message(lambda message: message.text == "/found")
async def cmd_lost(message: Message, state: FSMContext):
    await state.set_state(LostForm.photo)
    msg = await message.answer("📸 Please send a photo.")
    await state.update_data(last_bot_message=msg.message_id)

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

    state: FSMContext = dp.fsm.get_context(bot, inline_query.from_user.id, inline_query.from_user.id)
    current_state = await state.get_state()
    
    is_filter_context = current_state == "FilterForm:category"

    for key, title in CATEGORIES.items():
        if is_filter_context:
            count = get_category_item_count(key)
            if count == 0:
                continue
            result = InlineQueryResultArticle(
                id=key,
                title=title,
                input_message_content=InputTextMessageContent(
                    message_text=f"FILTER_CATEGORY:{key}"
                ),
                description=f"{count} items"
            )
        else:
            description = CATEGORY_DESCRIPTIONS.get(key, "")
            result = InlineQueryResultArticle(
                id=key,
                title=title,
                input_message_content=InputTextMessageContent(
                    message_text=f"SELECTED_CATEGORY:{key}"
                ),
                description=description
            )
        full_text = (title + " " + result.description).lower()
        if query in full_text:
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
    category_key = next(k for k, v in CATEGORIES.items() if v == data.get("category"))
    summary_for_lost = (
        f"Location: {data.get('location', '-')}\n"
        f"Comments: {data.get('comments', '-')}\n"
        f"Date: {datetime.now().date()}"
    )
    
    try:
        sent_msg = await bot.send_photo(
            chat_id="@lost_and_found_helper", 
            photo=data["photo"], 
            caption=summary_for_lost
        )
        
        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO found_items (message_id, category, date)
            VALUES (?, ?, ?)
        ''', (sent_msg.message_id, category_key, datetime.now()))
        conn.commit()
        conn.close()
        
        conn = sqlite3.connect("found_items.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT user_id FROM user_subscriptions
            WHERE category = ?
        ''', (category_key,))
        
        subscribers = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        for user_id in subscribers:
            try:
                notification_msg = await bot.send_photo(
                    chat_id=user_id,
                    photo=data["photo"],
                    caption=f"🔔 New item found in {data.get('category')}:\n\n{summary_for_lost}"
                )
                
                delete_btn = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="🗑️ Delete",
                        callback_data=f"notif_delete_{notification_msg.message_id}"
                    )
                ]])
                
                await bot.send_message(
                    chat_id=user_id,
                    text="This notification will auto-delete in 30 seconds",
                    reply_markup=delete_btn
                )
                
                asyncio.create_task(delete_notification(user_id, notification_msg.message_id))
                
            except Exception as e:
                print(f"Failed to notify user {user_id}: {e}")
        
        await callback.message.answer("✅ Form submitted successfully")
        
    except Exception as e:
        await callback.message.answer("⚠️ Failed to submit form")
        print(f"Submission error: {e}")
    
    await state.clear()
    await callback.answer()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    asyncio.run(main())
