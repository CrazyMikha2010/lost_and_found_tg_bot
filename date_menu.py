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

"""
/calendar sends calendar to choose date
"""

class CalendarForm(StatesGroup):
    viewing = State()

@dp.message(lambda message: message.text == "/calendar")
async def cmd_calendar(message: Message, state: FSMContext):
    """Показываем календарь на текущий месяц"""
    keyboard, year, month = generate_calendar_buttons(offset=0)
    title = f"🗓 Выберите день для {calendar.month_name[month]} {year}"
    msg = await message.answer(title, reply_markup=keyboard)
    await state.update_data(calendar_message=msg.message_id)
    await state.set_state(CalendarForm.viewing)

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
                week_row.append(InlineKeyboardButton(
                    text=str(day),
                    callback_data=f"select_day:{year}-{month:02d}-{day:02d}"
                ))
        buttons.append(week_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons), year, month

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

@dp.callback_query(CalendarForm.viewing, lambda c: c.data.startswith("select_day:"))
async def select_day_callback(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.replace("select_day:", "")
    year, month, day = map(int, date_str.split("-"))

    month_title = calendar.month_name[month]
    await callback.message.answer(f"📅 Вы выбрали: {day} {month_title}, {year}")
    await callback.answer()
