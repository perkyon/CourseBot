# user_handlers.py
import os
import re
import sqlite3

from aiogram import Router, F
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (FSInputFile, InlineKeyboardMarkup,
                           InlineKeyboardButton, CallbackQuery)

from yookassa import Configuration, Payment  # Не забудьте настроить Configuration где-то в main.py

from config import VERONIKA_ID  # берем ID из config, если хотим уведомлять Веронику

router = Router()

# ---------------------------------------------
# Состояния (FSM)
# ---------------------------------------------
class Registration(StatesGroup):
    name = State()
    email = State()
    phone = State()

# ---------------------------------------------
# Словарь курсов
# ---------------------------------------------
courses = {
    "course_1": {"title": "✨ Идеальный макияж", "price": 1490, "chat": "https://t.me/+CKm_e2SAXndjNDBi"},
    "course_2": {"title": "📋 Чек-лист косметики", "price": 990, "chat": "https://t.me/+8uSRRO1IucwzYjZi"},
    "course_3": {"title": "🌟 Оффлайн-курс", "price": 13000}
}

# ---------------------------------------------
# Хендлер команды /start
# ---------------------------------------------
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    video_file = "img/privetsvie.mp4"
    if os.path.exists(video_file):
        await message.answer_video(FSInputFile(video_file))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять условия", callback_data="accept_terms")],
        [InlineKeyboardButton(text="📜 Ознакомиться", callback_data="view_terms")]
    ])
    await message.answer("Перед регистрацией ознакомьтесь с условиями:", reply_markup=kb)

# ---------------------------------------------
# Хендлеры для Inline-кнопок «Ознакомиться» / «Отказаться»
# ---------------------------------------------
@router.callback_query(F.data == "view_terms")
async def terms(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять условия", callback_data="accept_terms")],
        [InlineKeyboardButton(text="❌ Отказаться", callback_data="decline_terms")]
    ])
    await callback.message.answer(
        "📜 Политика конфиденциальности:\nВаши данные используются только для регистрации и не передаются третьим лицам.",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data == "decline_terms")
async def decline_terms(callback: CallbackQuery):
    await callback.message.answer("❌ Вы отказались от условий. Регистрация отменена.")
    await callback.answer()

# ---------------------------------------------
# «Принять условия» → переходим к состоянию ввода имени
# ---------------------------------------------
@router.callback_query(F.data == "accept_terms")
async def accept_terms(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.name)
    await callback.message.answer("Введите ваше имя:")
    await callback.answer()

# ---------------------------------------------
# FSM: последовательный ввод данных (имя, email, телефон)
# ---------------------------------------------
@router.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.email)
    await message.answer("Введите ваш email:")

@router.message(Registration.email)
async def reg_email(message: types.Message, state: FSMContext):
    if "@" not in message.text:
        await message.answer("❌ Email должен содержать @. Повторите ввод:")
        return
    await state.update_data(email=message.text)
    await state.set_state(Registration.phone)
    await message.answer("Введите номер телефона (+7XXXXXXXXXX):")

@router.message(Registration.phone)
async def reg_phone(message: types.Message, state: FSMContext):
    if not re.match(r"^\+7\d{10}$", message.text):
        await message.answer("❌ Номер должен начинаться с +7 и содержать 11 цифр. Повторите ввод:")
        return

    data = await state.get_data()
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT OR REPLACE INTO users (tg_id, name, email, phone) VALUES (?,?,?,?)",
        (message.from_user.id, data['name'], data['email'], message.text)
    )
    conn.commit()
    conn.close()

    # Сбрасываем состояние (регистрация завершена)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать курс", callback_data="select_course")],
        [InlineKeyboardButton(text="Изменить данные", callback_data="accept_terms")]
    ])
    await message.answer(
        f"✅ Регистрация завершена!\n"
        f"Имя: {data['name']}\n"
        f"Email: {data['email']}\n"
        f"Телефон: {message.text}",
        reply_markup=kb
    )

# ---------------------------------------------
# Выбор курса
# ---------------------------------------------
@router.callback_query(F.data == "select_course")
async def select_course(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c["title"], callback_data=key)]
        for key, c in courses.items()
    ])
    await callback.message.answer("Выберите курс:", reply_markup=kb)
    await callback.answer()

# ---------------------------------------------
# Создание ссылки на оплату + обновление поля course
# ---------------------------------------------
@router.callback_query(F.data.in_(courses.keys()))
async def course_info(callback: CallbackQuery):
    course_key = callback.data
    course = courses[course_key]

    # Обновляем поле "course" в таблице users
    conn = sqlite3.connect("users.db")
    conn.execute("UPDATE users SET course=? WHERE tg_id=?", (course["title"], callback.from_user.id))
    conn.commit()
    conn.close()
    
    # Для диагностики:
    print("DEBUG: Current Yookassa config:", Configuration.account_id, Configuration.secret_key)

    # Создаём платёж в Yookassa
    payment = Payment.create({
        "amount": {"value": course["price"], "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://t.me/ВАШ_Бот"},
        "capture": True,
        "description": course["title"]
    })

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить курс 💳", url=payment.confirmation.confirmation_url)]
    ])

    await callback.message.answer(
        f"{course['title']} – {course['price']}₽",
        reply_markup=kb
    )

    # Отдельный случай: оффлайн-курс → уведомить Веронику
    if course_key == "course_3":
        user_link = (f"@{callback.from_user.username}"
                     if callback.from_user.username
                     else callback.from_user.full_name)
        await callback.message.bot.send_message(
            VERONIKA_ID,
            f"Новый покупатель оффлайн-курса: {user_link}"
        )

    await callback.answer()

def register_user_handlers(dp):
    """Регистрация роутера пользовательских хендлеров."""
    dp.include_router(router)
