"""
this is main and final code which i describes in readme
"""

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
from aiogram.exceptions import TelegramBadRequest
import asyncio

import sqlite3

from datetime import datetime, timedelta
import calendar


bot = Bot("YOUR BOT TOKEN HERE")
dp = Dispatcher()

# you can add your own categories, here's copy and paste form "": "",
CATEGORIES = {
    "daily broadcasts": "🔍 Обход дежурного менеджера",
    "pants": "👖 Штаны",
    "jackets": "🧥 Куртки",
    "sweaters": "🧣 Кофты",
    "shoes": "👟 Обувь",
    "bags": "🎒 Сумки",
    "bagsadv": "🛍️ Сумки с вещами внутри",
    "hats": "🎩 Головные уборы",
    "badges": "🎖️ Бейджики",
    "chargers_electronics": "🔌 Зарядки",
    "electronics_devices": "💻 Электроника",
    "accessories": "🕶️ Аксессуары",
    "sports_gear": "🎾 Спортинвентарь",
    "money_cards": "💰 Деньги и карты",
    "tshirts": "👕 Футболки",
    "winteracc": "🧢 Шапки и 🧤 Перчатки",
    "bevs": "💧 Фляжки",
    "other": "📦 Другое"
}

CATEGORY_DESCRIPTIONS = {
    "daily broadcasts": "ночной обход / фотографии с ресепшена",
    "pants": "джинсы / спортивные / шорты",
    "jackets": "",
    "sweaters": "толстовки / зипки / футболки",
    "shoes": "спортивная / неспортивная",
    "bags": "",
    "bagsadv": "сумки / шопперы / пакеты с вещами внутри",
    "hats": "шапки / кепки",
    "badges": "",
    "chargers_electronics": "",
    "electronics_devices": "компьютеры / телефоны / наушники",
    "accessories": "очки, кольца, ювелирка и тд",
    "sports_gear": "мячи, ракетки, гантели и тд",
    "money_cards": "",
    "tshirts": "футболки / майки",
    "winteracc": "шапки, перчатки, снуды и тп",
    "bevs": "фляжки / бутылки",
    "other": ""
}

"""
admins have more commands to use, so add their ids to list
to get id, text @getmyid_bot and paste code after <<Your user ID:>>
"""
ADMIN_IDS = set([0123456789, 9876543210])
ADMIN_EMOJI = "👮‍♂️"

def is_admin(user_id):
    return user_id in ADMIN_IDS

# classes for tracking states separately and asynchronous for each user

class FilterForm(StatesGroup):
    category = State()
    days = State()

class CalendarForm(StatesGroup):
    viewing = State()

class AdminForm(StatesGroup):
    broadcast = State()

class QuickBroadcastForm(StatesGroup):
    active = State()

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

class SearchState(StatesGroup): 
    viewing = State()

class NotificationForm(StatesGroup):
    action = State()
    subscribe = State()
    unsubscribe = State()

# gets all broadcasts made in corresponding date
def get_broadcasts_by_date(year, month, day):
    try:
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        date_str = f"{year}-{month:02d}-{day:02d}"

        cursor.execute('''
            SELECT message_id FROM found_items_let
            WHERE category = "daily broadcasts"
              AND DATE(date) = DATE(?)
            ORDER BY date DESC
        ''', (date_str,))

        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"Ошибка при получении сообщений: {e}")
        return []

# sends all broadcast messasges in corresponding day
@dp.callback_query(CalendarForm.viewing, lambda c: c.data.startswith("select_day:"))
async def select_day_callback(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.replace("select_day:", "")
    year, month, day = map(int, date_str.split("-"))

    broadcasts = get_broadcasts_by_date(year, month, day)

    if not broadcasts:
        await callback.answer("❌ Нет записей за этот день", show_alert=True)
        return

    sent_messages = []

    for msg_id in broadcasts:
        try:
            sent_msg = await bot.forward_message(
                chat_id=callback.message.chat.id,
                from_chat_id="@help_channel_name",
                message_id=msg_id
            )
            sent_messages.append(sent_msg.message_id)
        except Exception as e:
            print(f"Не удалось переслать сообщение {msg_id}: {e}")

    hide_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Скрыть всё", callback_data="hide_daily_all")]
    ])
    hide_msg = await callback.message.answer("Нажмите, чтобы скрыть всё:", reply_markup=hide_button)

    await state.update_data(
        sent_daily_messages=sent_messages,
        hide_daily_button=hide_msg.message_id
    )

    await callback.answer(f"Показано {len(broadcasts)} сообщений")

# /quickstart command handling
@dp.message(lambda message: message.text == "/quickstart")
async def cmd_quickstart(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не админ")
        return

    msg = await message.answer("🟢 Режим бродкаста включен.\nОтправляйте фото или фото с описаниями для публикации в daily broadcast.\nИспользуй /quickstop для выхода из режима.")
    await state.update_data(broadcast_mode=True, broadcast_prompt=msg.message_id, broadcast_command=message.message_id)
    await state.set_state(QuickBroadcastForm.active)

# handling of send during broadcast mode messages
@dp.message(QuickBroadcastForm.active)
async def handle_broadcast_message(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/"):
        await state.set_state(None)
        if message.text == "/quickstop":
            data = await state.get_data()

            prompt_id = data.get('broadcast_prompt')
            if prompt_id:
                try:
                    await bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)
                except Exception:
                    pass

            command_id = data.get('broadcast_command')
            if command_id:
                try:
                    await bot.delete_message(chat_id=message.chat.id, message_id=command_id)
                except Exception:
                    pass
            
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            except Exception:
                pass

            await state.clear()
            await message.answer("🔴 Бродкаст остановлен.")
        return

    user_id = message.from_user.id
    
    if not message.photo:
        error_msg = await message.answer("⚠️ Пожалуйста отправьте фото.")
        await asyncio.sleep(3)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=error_msg.message_id)
        except Exception:
            pass
        return

    photo = message.photo[-1].file_id
    caption = message.caption or "---"

    conn = sqlite3.connect("found_items_let.db")  
    cursor = conn.cursor()

    try:
        sent_msg = await bot.send_photo(
            chat_id="@help_channel_name",
            photo=photo,
            caption=f"📢 Daily Broadcast\n{caption}\n📅 {datetime.now().date()}"
        )
        cursor.execute('''
            INSERT INTO found_items_let (category, message_id, date)
            VALUES (?, ?, ?)
        ''', (
            "daily broadcasts",
            sent_msg.message_id,
            datetime.now().date()
        ))
        conn.commit()

        confirm = await message.answer("✅ Сообщение отправлено")
        await asyncio.sleep(2)
        await bot.delete_message(chat_id=message.chat.id, message_id=confirm.message_id)

    except Exception as e:
        print(f"Error in broadcast mode: {e}")
        error = await message.answer("❌ Не получилось отправить ваше сообщение")
        await asyncio.sleep(3)
        await bot.delete_message(chat_id=message.chat.id, message_id=error.message_id)

    finally:
        conn.close()

# easter egg:) tbh i'm just proud of my calendar creation
@dp.message(lambda message: message.text == "/calendar")
async def cmd_calendar(message: Message, state: FSMContext):
    keyboard, year, month = generate_calendar_buttons(offset=0)
    title = f"🗓 Выберите день для {calendar.month_name[month]} {year}"
    msg = await message.answer(title, reply_markup=keyboard)
    await state.update_data(calendar_message=msg.message_id)
    await state.set_state(CalendarForm.viewing)

@dp.callback_query(CalendarForm.viewing, lambda c: c.data.startswith("select_day:"))
async def select_day_callback(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.replace("select_day:", "")
    year, month, day = map(int, date_str.split("-"))

    month_title = calendar.month_name[month]
    await callback.message.answer(f"📅 Вы выбрали: {day} {month_title}, {year}")
    await callback.answer()

# generates all buttons for calendar
def generate_calendar_buttons(offset=0):
    today = datetime.now()
    year = today.year
    month = today.month + offset

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    buttons = []

    buttons.append([
        InlineKeyboardButton(text="⬅️", callback_data=f"cal_prev:{offset}"),
        InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text="➡️", callback_data=f"cal_next:{offset}")
    ])

    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    buttons.append([InlineKeyboardButton(text=d, callback_data="ignore") for d in week_days])

    for week in month_days:
        week_row = []
        for day in week:
            if day == 0:
                week_row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                has_content = check_if_has_content_for_day(year, month, day)
                text = str(day) if has_content else "❌"

                week_row.append(InlineKeyboardButton(
                    text=text,
                    callback_data=f"select_day:{year}-{month:02d}-{day:02d}"
                ))
        buttons.append(week_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons), year, month

# handle arrows for changing months
@dp.callback_query(CalendarForm.viewing, lambda c: c.data.startswith(("cal_prev", "cal_next")))
async def navigate_month(callback: CallbackQuery, state: FSMContext):
    offset = int(callback.data.split(":")[1])
    if "cal_prev" in callback.data:
        offset -= 1
    elif "cal_next" in callback.data:
        offset += 1

    keyboard, year, month = generate_calendar_buttons(offset)
    title = f"🗓 Выберите дату для {calendar.month_name[month]} {year}"
    try:
        await callback.message.edit_text(title, reply_markup=keyboard)
    except Exception as e:
        print(f"Ошибка редактирования календаря: {e}")
    await callback.answer()

# cleares all sent messages in broadcast
@dp.callback_query(lambda c: c.data == "hide_daily_all")
async def handle_hide_daily_all(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    for msg_id in data.get("sent_daily_messages", []):
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение {msg_id}: {e}")

    try:
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=data.get("hide_daily_button")
        )
    except Exception:
        pass

    await callback.answer("✅ Все сообщения скрыты")
    
# helper func for checking if day has broadcasts on it or no
def check_if_has_content_for_day(year, month, day):
    try:
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        date_str = f"{year}-{month:02d}-{day:02d}"

        cursor.execute('''
            SELECT COUNT(*) FROM found_items_let
            WHERE category = "daily broadcasts"
              AND DATE(date) = DATE(?)
        ''', (date_str,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Ошибка при проверке контента за {date_str}: {e}")
        return False

# start command
@dp.message(lambda message: message.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    conn = sqlite3.connect("found_items_let.db")
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', 
                  (message.from_user.id,))
    conn.commit()
    conn.close()
    
    welcome_text = (
        "👋 Привет! Это школьный бот Lost&Found.\n\n"
        "🔍 Если ты потерял вещь — используй /lost\n"
        "📦 Если нашёл чужую вещь — используй /found\n\n"
        "❗️Также не забывай, что в чате есть модерация объявлений, "
        "так что не стоит писать ничего лишнего или не относящегося к теме:)\n\n"
        "Узнай о функциях бота с помощью /help\n\n"
        "При любых ошибках бота или для коммуникации пишите @miha19652010"
    )

    try:
        await message.answer(welcome_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Failed to send welcome message: {e}")
        await message.answer(welcome_text, parse_mode=ParseMode.HTML)

# help command
@dp.message(lambda message: message.text == "/help")
async def help_command(message: Message):
    help_text = (
        "🔍 <b>Как пользоваться ботом</b>\n\n"
        
        "<b>1. /lost — Поиск потерянных вещей</b>\n"
        "• Выберите категорию (джинсы, куртки, обувь и др.)\n"
        "• Укажите период поиска (сколько дней назад)\n"
        "• Бот покажет все подходящие объявления из базы\n"
        "• Каждое объявление содержит: фото, описание и дату\n\n"
        
        "<b>2. /found — Сообщить о найденной вещи</b>\n"
        "• Отправьте фото предмета\n"
        "• Укажите категорию (например: рюкзаки, электроника, украшения)\n"
        "• Добавьте место и комментарий (опционально)\n"
        "• Объявление появится в общем списке\n"
        "• Подписчики получат уведомление о вашей находке\n\n"
        
        "<b>3. /notification — Управление уведомлениями</b>\n"
        "• Подписывайтесь на интересующие категории\n"
        "• Получайте уведомления о новых находках в формате фото + описание\n"
        "• Каждое уведомление можно удалить нажатием на 🗑️\n"
        "• Изменяйте подписки в любое время\n\n"
        
        "<b>🎯 Полезные советы</b>\n"
        "• Всегда добавляйте четкое фото при создании объявления\n"
        "• Чем точнее категория и описание — тем выше шанс найти владельца\n"
        "• Подписывайтесь только на нужные категории, чтобы не получать спам\n"
        "• Администраторы могут отправлять объявления всем пользователям\n\n"
        "При любых ошибках бота или для коммуникации пишите @miha19652010\n\n"

        "<b>❓ Как начать?</b>\n"
        "• Используйте команды в меню\n"
        "• Или нажмите на соответствующую кнопку ниже"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 /lost", callback_data="help_lost"),
            InlineKeyboardButton(text="📦 /found", callback_data="help_found"),
            InlineKeyboardButton(text="🔔 /notification", callback_data="help_notifications")
        ],
        [InlineKeyboardButton(text="📚 Все команды", callback_data="all_commands")]
    ])
    
    try:
        await message.answer(help_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.answer(help_text.replace("<b>","").replace("</b>",""), reply_markup=keyboard)

# more explicit help commands
@dp.callback_query(lambda c: c.data in ["help_lost", "help_found", "help_notifications", "all_commands"])
async def handle_help_sections(callback: CallbackQuery):
    section = callback.data.split("_")[1]
    content = "❌ Неизвестный раздел помощи"


    if section == "lost":
        content = (
            "🔍 <b>Как использовать /lost</b>\n\n"
            "1. Введите команду /lost\n"
            "2. Выберите интересующую вас категорию\n"
            "3. Укажите период поиска (например: 7 дней)\n"
            "4. Бот покажет все подходящие объявления\n"
            "5. Нажмите 🗑️ чтобы скрыть объявления\n\n"
            "💡 Совет: Используйте фильтрацию по дате чтобы видеть самые свежие объявления"
        )
    elif section == "found":
        content = (
            "📦 <b>Как использовать /found</b>\n\n"
            "1. Введите команду /found\n"
            "2. Отправьте фото найденной вещи\n"
            "3. Выберите категорию из предложенных\n"
            "4. Добавьте место и комментарий (необязательно)\n"
            "5. Подтвердите отправку объявления\n\n"
            "✅ После подтверждения объявление появится в общем списке\n"
            "🔔 Подписчики на эту категорию получат уведомление"
        )
    elif section == "notifications":
        content = (
            "🔔 <b>Уведомления о находках</b>\n\n"
            "1. Введите /notification\n"
            "2. Выберите '🔔 Подписаться'\n"
            "3. Найдите нужную категорию через поиск\n"
            "4. Чтобы отписаться - выберите '🔕 Отписаться' и нужные категории\n"
            "5. Уведомления будут приходить в течение 30 секунд после публикации\n\n"
            "🗑️ Каждое уведомление можно удалить нажатием на кнопку"
        )
    elif section == "commands":
        content = (
            "📚 <b>Все команды бота</b>\n\n"
            "🔹 /start - Начать работу с ботом\n"
            "🔹 /help - Помощь и описание функций\n"
            "🔹 /lost - Найти потерянную вещь\n"
            "🔹 /found - Сообщить о найденной вещи\n"
            "🔹 /notification - Управление уведомлениями\n\n"
            "🔐 <b>Для администраторов:</b>\n"
            "🔹 /showall - Посмотреть все объявления\n"
            "🔹 /sendall - Отправить сообщение всем пользователям"
        )
    try:
        await callback.message.edit_text(content, parse_mode=ParseMode.HTML)
        await callback.answer()
    except Exception as e:
        print(f"Error updating help text: {e}")
        await callback.answer("Ошибка отображения справки")

# admin func to show all messages in db and delete them by button click
@dp.message(lambda message: message.text == "/showall")
async def cmd_showall(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    conn = sqlite3.connect("found_items_let.db")
    cursor = conn.cursor()
    cursor.execute('SELECT message_id, category, date FROM found_items_let ORDER BY date DESC')
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        await message.answer("Ничего не нашли в БД")
        return
    sent_messages = []
    for msg_id, category, date in results:
        try:
            temp_msg = await bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id="@help_channel_name",
                message_id=msg_id
            )
            
            caption = temp_msg.caption or ""
            
            location = "-"
            comments = "-"
            
            for line in caption.split("\n"):
                if line.startswith("Место:"):
                    location = line.replace("Место:", "").strip()
                elif line.startswith("Комментарии:"):
                    comments = line.replace("Комментарии:", "").strip()
            
            delete_kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🗑️ Удалить из БД",
                    callback_data=f"admin_delete_{msg_id}"
                )
            ]])
            
            sent_msg = await message.answer_photo(
                photo=temp_msg.photo[-1].file_id if temp_msg.photo else None,
                caption=(
                    f"Категория: {category}\n"
                    f"Место: {location}\n"
                    f"Комментарии: {comments}\n"
                    f"Дата: {date}"
                ),
                reply_markup=delete_kb
            )
            
            sent_messages.append(sent_msg.message_id)
            
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=temp_msg.message_id
            )
            
        except Exception as e:
            print(f"Error showing message {msg_id}: {e}")
    
    cleanup_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🧹 Hide All",
            callback_data="admin_cleanup"
        )
    ]])

    end_list = await message.answer("Конец списка", reply_markup=cleanup_kb)
    await state.update_data(
        sent_messages=sent_messages,
        end_list_message=end_list.message_id,
    )
    
# handle admin deletion of item from db
@dp.callback_query(lambda c: c.data.startswith("admin_delete_"))
async def handle_admin_delete(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Unauthorized")
        return

    msg_id = callback.data.split("_")[2]

    try:
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        cursor.execute('DELETE FROM found_items_let WHERE message_id = ?', (msg_id,))
        conn.commit()
        conn.close()

        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
        except Exception as e:
            print(f"Failed to delete admin message: {e}")

        success_msg = await callback.message.answer(
            f"🗑️ Сообщение {msg_id} удалено из БД"
        )
        asyncio.create_task(delete_after_delay(
            chat_id=success_msg.chat.id,
            message_id=success_msg.message_id,
            delay=5
        ))

    except Exception as e:
        await callback.answer(f"❌ Ошибка удаления сообщения: {str(e)}")
        print(f"Error during admin deletion: {e}")

# deletes sent to admin messages
@dp.callback_query(lambda c: c.data == "admin_cleanup")
async def handle_admin_cleanup(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Unauthorized")
        return
    
    try:
        data = await state.get_data()
        message_ids = data.get("sent_messages", [])
        hide_msg_id = data.get("end_list_message")

        for msg_id in message_ids:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=msg_id
                )
            except TelegramBadRequest as e:
                if "message to delete not found" in str(e):
                    print(f"Message {msg_id} already deleted")
                else:
                    print(f"Failed to delete message {msg_id}: {e}")

        if hide_msg_id:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=hide_msg_id
                )
            except Exception as e:
                print(f"Failed to delete hide button: {e}")
        
    except Exception as e:
        print(f"Cleanup error: {e}")
    
    await callback.answer("Очистка закончена")

# admin func to send everyone who used bot a specific message
@dp.message(lambda message: message.text == "/sendall")
async def cmd_sendall(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    await message.answer("Отправьте сообщения для всех пользователей:")
    await state.set_state(AdminForm.broadcast)

# proccesses sending message to all users
@dp.message(AdminForm.broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    conn = sqlite3.connect("found_items_let.db")
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()

    success = 0
    failed = 0

    admin_badge = f"{ADMIN_EMOJI} *Сообщение от администратора:*\n\n"

    if message.text:
        full_text = admin_badge + message.text
        for user_id in users:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=full_text,
                    parse_mode=ParseMode.MARKDOWN
                )
                success += 1
            except Exception:
                failed += 1

    elif message.photo:
        photo_file_id = message.photo[-1].file_id
        caption = message.caption or ""
        full_caption = admin_badge + caption

        for user_id in users:
            try:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo_file_id,
                    caption=full_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
                success += 1
            except Exception:
                failed += 1

    else:
        await message.answer("Неподдерживаемая форма сообщения.")
        await state.clear()
        return

    stats_text = (
        f"{ADMIN_EMOJI} Broadcast completed:\n"
        f"✅ Successfully delivered: {success}\n"
        f"❌ Failed attempts: {failed}"
    )

    await message.answer(stats_text)
    await state.clear()

# initialises database (creates a file and builds tables in it)
def init_db():
    conn = sqlite3.connect("found_items_let.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS found_items_let (
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# deletes sent to user notification message
@dp.callback_query(lambda c: c.data.startswith("notif_delete_"))
async def handle_notification_delete(callback: CallbackQuery):
    msg_id = int(callback.data.split("_")[-1])
    
    try:
        await bot.delete_message(callback.message.chat.id, msg_id)
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting notification: {e}")
    
    await callback.answer("Напоминение спрятано.")

# handles notification command
@dp.message(lambda message: message.text == "/notification")
async def cmd_notification(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Подписаться", callback_data="notify_subscribe")],
        [InlineKeyboardButton(text="🔕 Отписаться", callback_data="notify_unsubscribe")]
    ])
    what_would_msg = await message.answer("Что ты хочешь сделать?", reply_markup=keyboard)
    await state.update_data(what_would_message=what_would_msg.message_id)
    await state.update_data(notification_message=message)
    await state.set_state(NotificationForm.action)

# handles subscribe and unsubscribe
@dp.callback_query(lambda c: c.data in ["notify_subscribe", "notify_unsubscribe"])
async def handle_notification_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]

    data = await state.get_data()
    what_would_msg_id = data.get("what_would_message")
    
    if what_would_msg_id:
        try:
            await bot.delete_message(
                chat_id=data.get("notification_message").chat.id,
                message_id=what_would_msg_id
            )
        except Exception as e:
            print(f"Failed to delete search prompt message: {e}")
    
    if action == "subscribe":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔍  Выбери категорию",
                switch_inline_query_current_chat="NOTIFY_SUBSCRIBE: "
            )]
        ])
        search_prompt_msg = await callback.message.answer("Выбери категорию для подписки:", reply_markup=keyboard)
        await state.update_data(search_prompt_message=search_prompt_msg.message_id)
        await state.set_state(NotificationForm.subscribe)
    else:
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT category FROM user_subscriptions
            WHERE user_id = ?
        ''', (callback.from_user.id,))
        
        subscriptions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not subscriptions:
            await callback.message.answer("У тебя нет активных подписок.")
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
                text="✅ Финиш", 
                callback_data="unsub_finish"
            )
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer("Нажми на категорию для отписки:", reply_markup=keyboard)
        await state.set_state(NotificationForm.unsubscribe)

# extracts category to subscribe from inline query
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

# finishes subscription proccess:
#     adds user to db 
#     sends confirmation 
@dp.message(NotificationForm.subscribe, lambda m: m.text.startswith("SELECTED_SUB:"))
async def handle_subscription_selection(message: Message, state: FSMContext):
    raw = message.text.replace("SELECTED_SUB:", "").strip()
    category = CATEGORIES.get(raw, None)
    
    if not category:
        await message.answer("Не правильная категория выбрана")
        return
    
    user_id = message.from_user.id
    
    try:
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO user_subscriptions (user_id, category)
            VALUES (?, ?)
        ''', (user_id, raw))
        conn.commit()
        conn.close()
        
        success_msg = await message.answer(f"✅ Подписался на {category} напоминания!")

        asyncio.create_task(delete_after_delay(
            chat_id=message.chat.id,
            message_id=success_msg.message_id,
            delay=15
        ))
    except Exception as e:
        await message.answer("❌ Не смогли оформить подписку")
        print(f"Subscription error: {e}")

    try:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception as e:
        print(f"Failed to delete SELECTED_SUB message: {e}")

    data = await state.get_data()
    search_prompt_msg_id = data.get("search_prompt_message")
    
    if search_prompt_msg_id:
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=search_prompt_msg_id
            )
        except Exception as e:
            print(f"Failed to delete search prompt message: {e}")
    
    
    await state.clear()

# handles unsubscribe (same as subscribe)
@dp.callback_query(lambda c: c.data.startswith("unsub_"))
async def handle_unsubscribe(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_", 1)[1]
    
    if data == "finish":
        await callback.message.delete()
        success_msg = await callback.message.answer("✅ Настройки подписки обновлены")
        asyncio.create_task(delete_after_delay(
            chat_id=success_msg.chat.id,
            message_id=success_msg.message_id,
            delay=15
        ))
        await state.clear()
        return
    
    category = data
    user_id = callback.from_user.id
    
    try:
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM user_subscriptions
            WHERE user_id = ? AND category = ?
        ''', (user_id, category))
        conn.commit()
        conn.close()
        
        conn = sqlite3.connect("found_items_let.db")
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
                text="✅ Финиш", 
                callback_data="unsub_finish"
            )
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        
    except Exception as e:
        await callback.answer("Ошибка обновления подписки")
        print(f"Unsubscription error: {e}")

# counts items in corresponding category for inline query description
def get_category_item_count(category_key):
    try:
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM found_items_let WHERE category = ?
        ''', (category_key,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"Error getting category count: {e}")
        return 0

# in lost filter returns all file ids in corresponding time range and category
def get_message_ids_by_category_and_days(category, max_days_back):
    try:
        cutoff_date = (datetime.now() - timedelta(days=int(max_days_back))).date()
        
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT message_id 
            FROM found_items_let
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

# handle lost command
@dp.message(lambda message: message.text == "/lost")
async def cmd_filter(message: Message, state: FSMContext):
    prompt_msg = await message.answer("🔍 Какую категорию ты хочешь увидеть?")
    await state.update_data(last_bot_message=prompt_msg.message_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔍 Выбери категорию",
            switch_inline_query_current_chat=" "
        )]
    ])
    search_msg = await message.answer("Найди категорию:", reply_markup=keyboard)
    await state.update_data(search_prompt_message=search_msg.message_id)
    await state.set_state(FilterForm.category)

# handle filtering category
@dp.message(FilterForm.category, lambda m: m.text.startswith("FILTER_CATEGORY:"))
async def handle_filter_category(message: Message, state: FSMContext):
    raw = message.text.replace("FILTER_CATEGORY:", "").strip()
    await state.update_data(filter_category=raw)
    
    data = await state.get_data()
    for msg_key in ['last_bot_message', 'search_prompt_message']:
        msg_id = data.get(msg_key)
        if msg_id:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            except Exception as e:
                print(f"Failed to delete message {msg_key}: {e}")

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass
    # specific calendar opens for daily broadcasts
    if raw == "daily broadcasts":
        keyboard, year, month = generate_calendar_buttons(offset=0)
        title = f"🗓 Выберите день для {calendar.month_name[month]} {year}"
        msg = await message.answer(title, reply_markup=keyboard)
        await state.update_data(calendar_message=msg.message_id)
        await state.set_state(CalendarForm.viewing)
    else:
        days_msg = await message.answer("📅 На сколько дней назад вы бы хотели видеть объявления?")
        await state.update_data(days_message=days_msg.message_id)
        await state.set_state(FilterForm.days)

# asks for time range
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
        await message.answer(f"Ничего не нашли в этой категории в последние {days} дней.")
        await state.clear()
        return

    sent_messages = []
    
    for msg_id in message_ids:
        try:
            sent_msg = await bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id="@help_channel_name",
                message_id=msg_id
            )
            sent_messages.append(sent_msg.message_id)
        except Exception as e:
            print(f"Error sending message {msg_id}: {e}")

    hide_orders_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Спрятать объявление", callback_data="hide_orders")]
    ])
    
    hide_msg = await message.answer("Нажмите на кнопку чтобы скрыть все объявления:", reply_markup=hide_orders_button)
    
    await state.update_data(
        sent_messages=sent_messages,
        hide_button_message=hide_msg.message_id
    )
    await state.set_state(SearchState.viewing)

# hides all sent orders in lost func
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
    await callback.answer("Все сообщения спрятаны")

# handles found func
@dp.message(lambda message: message.text == "/found")
async def cmd_lost(message: Message, state: FSMContext):
    await state.set_state(LostForm.photo)
    msg = await message.answer("📸 Пожалуйста отправьте фото.")
    await state.update_data(last_bot_message=msg.message_id)

# asks for photo
@dp.callback_query(lambda c: c.data == "makeOrder")
async def start_make_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LostForm.photo)
    await callback.message.edit_text("📸 Пожалуйста отправьте фото.")
    await state.update_data(last_bot_message=callback.message.message_id)

# receives photo and cleans chat, switches to choosing category
@dp.message(LostForm.photo)
async def receive_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста отправьте подходящее фото.")
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
            text="🔍 Выбери категорию",
            switch_inline_query_current_chat=" "
        )]
    ])
    msg = await message.answer("Найди категорию:", reply_markup=keyboard)
    await state.update_data(last_bot_message=msg.message_id)
    await state.set_state(LostForm.category)

# handles inline query for choosing category
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
            if key == "daily broadcasts":
                continue
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

# handles choosing category
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

# shows summary
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
        f"📄 <b>Твоя форма:</b>\n"
        f"<b>Категория:</b> {data.get('category', '-')}\n"
        f"<b>Место:</b> {data.get('location', '-')}\n"
        f"<b>Комментарии:</b> {data.get('comments', '-')}"
    )

    confirm_buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить & Отправить", callback_data="confirm_submit")],
        [
            InlineKeyboardButton(
                text="📷 Изменить Фото" if data.get("photo") else "📸 Добавить Фото",
                callback_data="edit_photo"
            ),
            InlineKeyboardButton(
                text="🏷️ Изменить категорию" if data.get("category") else "🔍 Добавить Категорию",
                callback_data="edit_category"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Изменить место" if data.get("location") else "📍 Добавить место",
                callback_data="edit_location"
            ),
            InlineKeyboardButton(
                text="💬 Изменить комментарий" if data.get("comments") else "📝 Добавить комментарий",
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

    new_buttons_msg = await message.answer("Все верно?", reply_markup=confirm_keyboard)

    await state.update_data(
        summary_message=new_summary_msg.message_id,
        buttons_message=new_buttons_msg.message_id
    )

# handles editing for each action
@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def handle_edit(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("edit_", "")

    if action == "photo":
        msg = await callback.message.answer("📸 Пожалуйста отправьте новое фото.")
        await state.update_data(last_bot_message=msg.message_id)
        await state.set_state(EditingForm.photo)
    elif action == "category":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔍 Выбери категорию",
                switch_inline_query_current_chat=" "
            )]
        ])
        msg = await callback.message.answer("Найди категорию:", reply_markup=keyboard)
        await state.update_data(last_bot_message=msg.message_id)
        await state.set_state(EditingForm.category)
    elif action == "location":
        msg = await callback.message.answer("Где было потеряно? (Отправьте `-` для пропуска)")
        await state.update_data(last_bot_message=msg.message_id)
        await state.set_state(EditingForm.location)
    elif action == "comments":
        msg = await callback.message.answer("Добавьте или поменяйте комментарий: (Отправьте `-` для пропуска)")
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

# updates photo
@dp.message(EditingForm.photo)
async def update_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста отправьте подходящее фото.")
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

# updates category
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

# updates location
@dp.message(EditingForm.location)
async def update_location(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await message.answer("Пропустил изменение места.")
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

# updates comments
@dp.message(EditingForm.comments)
async def update_comments(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await message.answer("Пропустил изменение комментария.")
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

# confirm submission handling
@dp.callback_query(lambda c: c.data == "confirm_submit")
async def confirm_submission(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category_key = next(k for k, v in CATEGORIES.items() if v == data.get("category"))
    summary_for_lost = (
        f"Место: {data.get('location', '-')}\n"
        f"Комментарий: {data.get('comments', '-')}\n"
        f"Дата: {datetime.now().date()}"
    )
    
    try:
        sent_msg = await bot.send_photo(
            chat_id="@help_channel_name", 
            photo=data["photo"], 
            caption=summary_for_lost
        )
        
        conn = sqlite3.connect("found_items_let.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO found_items_let (message_id, category, date)
            VALUES (?, ?, ?)
        ''', (sent_msg.message_id, category_key, datetime.now()))
        conn.commit()
        conn.close()
        
        conn = sqlite3.connect("found_items_let.db")
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
                    caption=f"🔔 Новая вещь найдена в {data.get('category')}:\n\n{summary_for_lost}"
                )
                
                delete_btn = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="🗑️ Спрятать",
                        callback_data=f"notif_delete_{notification_msg.message_id}"
                    )
                ]])
                
                await bot.send_message(
                    chat_id=user_id,
                    text="Нажмите ниже чтобы спрятать объявление",
                    reply_markup=delete_btn
                )

                
            except Exception as e:
                print(f"Failed to notify user {user_id}: {e}")
        
        
        success_msg = await callback.message.answer("✅ Форма заполнена успешно")

        summary_msg_id = data.get('summary_message')
        buttons_msg_id = data.get('buttons_message')

        if summary_msg_id:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=summary_msg_id)
            except Exception as e:
                print(f"Failed to delete summary message: {e}")

        if buttons_msg_id:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=buttons_msg_id)
            except Exception as e:
                print(f"Failed to delete buttons message: {e}")

        asyncio.create_task(delete_after_delay(
            chat_id=callback.message.chat.id,
            message_id=success_msg.message_id,
            delay=15
        ))
        
    except Exception as e:
        await callback.message.answer("⚠️ Не получилось загрузить форму")
        print(f"Submission error: {e}")
    
    await state.clear()
    await callback.answer()

async def delete_after_delay(chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Failed to auto-delete message {message_id}: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    asyncio.run(main())

    
