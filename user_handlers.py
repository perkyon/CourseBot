# user_handlers.py

import os
import re
import sqlite3

from aiogram import Router, F
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from yookassa import Payment, Configuration

# Импортируем ID админа из config.py, чтобы отправлять ему данные
from config import (
    ADMIN_ID,   # нужно прописать в config.py
    VERONIKA_ID,
    TAX_SYSTEM_CODE,
    VAT_CODE
)

router = Router()

# ---------------------------------------------
# Состояния (FSM)
# ---------------------------------------------
class Registration(StatesGroup):
    name = State()
    email = State()
    phone = State()


# ---------------------------------------------
# Словари с подробными текстами курса
# ---------------------------------------------

# Краткое описание (для шага «Выберите курс»)
courses_short_info = {
    "course_1": "✨ Твой идеальный макияж на каждый день\nНаучись создавать лёгкий, но эффектный образ! Освоишь базовые техники, подготовку кожи, коррекцию и макияж глаз и губ. Включает чек-лист с проверенной косметикой.",
    "course_2": "📋 Чек-лист «Необходимых косметических средств»\nСэкономь время и деньги – получи список лучших бюджетных и премиальных средств, подходящих именно тебе.",
    "course_3": "🌟 OFFLINE COURSE «МАКИЯЖ ДЛЯ СЕБЯ»\nПолное погружение в макияж с индивидуальным подходом. Разберём косметичку, освоим стойкую коррекцию и создадим идеальный вечерний образ. Косметика и кисти включены!"
}

# Полное описание (для показа в show_course_details)
courses_full_info = {
    "course_1": (
        "✨ Твой идеальный макияж на каждый день\n\n"
        "Этот курс поможет тебе освоить базовые техники макияжа и научиться создавать лёгкий, но эффектный образ.\n\n"
        "📌 Что тебя ждёт?\n"
        "🔹 Подготовка кожи – правильное очищение и увлажнение\n"
        "🔹 Коррекция лица – кремовые vs. сухие текстуры\n"
        "🔹 Макияж глаз и губ – подбираем оттенки, осваиваем техники для выразительного, но естественного образа\n\n"
        "💡 Бонус – чек-лист с лучшими средствами!\n\n"
        "После курса ты сможешь делать стойкий макияж без лишних трат и ошибок. 💄✨\n\n"
        "💰 Стоимость: 1490 ₽"
    ),
    "course_2": (
        "📋 Чек-лист «Необходимых косметических средств»\n\n"
        "Не трать деньги на бесполезную косметику! Этот чек-лист поможет выбрать лучшие средства именно для тебя.\n\n"
        "📌 Что внутри?\n"
        "✔ Бюджетные и премиальные продукты, которые действительно работают\n"
        "✔ Средства для разных типов кожи\n"
        "✔ Проверенные позиции, которые я использую сама и рекомендую клиентам\n\n"
        "Ты больше не будешь разочаровываться в покупке косметики – сразу выберешь качественные продукты!\n\n"
        "💰 Стоимость: 990 ₽"
    ),
    "course_3": (
        "🌟 OFFLINE COURSE «МАКИЯЖ ДЛЯ СЕБЯ»\n\n"
        "Индивидуальное обучение: разберёшься в косметике, научишься подбирать продукты и создавать макияж без визажиста.\n\n"
        "📌 Формат\n"
        "✔ 2 дня по 2 часа (теория + практика)\n"
        "✔ Косметика и кисти предоставляются\n"
        "✔ Гибкий график\n\n"
        "💄 День 1 – База идеального макияжа\n"
        "🔹 Разбор косметички\n"
        "🔹 Тестируем разные бренды\n"
        "🔹 Подбор по типу кожи\n"
        "🔹 Дневной макияж\n\n"
        "✨ День 2 – Совершенствуем навык\n"
        "🔹 Вечерний макияж\n"
        "🔹 ТОП-5 кистей\n"
        "🔹 Стойкая кремовая коррекция\n"
        "🔹 Wish-list косметики под твой бюджет\n\n"
        "После курса ты сможешь делать проф. макияж самостоятельно! 💄✨\n\n"
        "💰 Стоимость: 13000 ₽"
    )
}

# Цены и названия для кода (Payment)
courses_data = {
    "course_1": {"title": "✨ Твой идеальный макияж", "price": 1490},
    "course_2": {"title": "📋 Чек-лист косметики", "price": 990},
    "course_3": {"title": "🌟 Оффлайн-курс", "price": 13000}
}

# ---------------------------------------------
# Хендлер /start
# ---------------------------------------------
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    video_file = "img/privetsvie.mp4"
    if os.path.exists(video_file):
        await message.answer_video(FSInputFile(video_file))

    text = (
        "Перед регистрацией ознакомьтесь с условиями:\n\n"
        "1) Мы собираем ваше ФИО, Email, Телефон только для оформления чека (54‑ФЗ).\n"
        "2) Данные не передаются третьим лицам и используются только для выдачи чека.\n"
        "3) Вы можете запросить изменение или удаление ваших данных.\n"
        "4) Полная политика конфиденциальности... (и т.д.)"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять условия", callback_data="accept_terms")],
        [InlineKeyboardButton(text="❌ Отказаться", callback_data="decline_terms")]
    ])
    await message.answer(text, reply_markup=kb)

# ---------------------------------------------
# Отказ и принятие условий
# ---------------------------------------------
@router.callback_query(F.data == "decline_terms")
async def decline_terms(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("❌ Вы отказались от условий. Регистрация отменена.")
    await callback.answer()

@router.callback_query(F.data == "accept_terms")
async def accept_terms(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    # Задаём вопрос «Введите ваше имя»
    sent_msg = await callback.message.answer("Введите ваше имя:")
    # Сохраняем message_id, чтобы потом удалить
    await state.update_data({"last_bot_msg_id": sent_msg.message_id})

    await state.set_state(Registration.name)
    await callback.answer()

# ---------------------------------------------
# FSM: Имя → Email → Телефон
# ---------------------------------------------
class Registration(StatesGroup):
    name = State()
    email = State()
    phone = State()

@router.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # Удаляем предыдущий вопрос
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_id)
        except:
            pass

    # Удаляем ответ пользователя
    await message.delete()

    # Сохраняем имя
    await state.update_data({"name": message.text})

    # Следующий вопрос
    sent_msg = await message.answer("Введите ваш Email (пример: name@example.com):")
    await state.update_data({"last_bot_msg_id": sent_msg.message_id})
    await state.set_state(Registration.email)

@router.message(Registration.email)
async def reg_email(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # Удаляем предыдущий вопрос
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_id)
        except:
            pass

    # Удаляем ответ пользователя
    await message.delete()

    # Проверяем email
    email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    if not email_pattern.match(message.text):
        sent_msg = await message.answer("❌ Неверный формат Email. Пример: user@example.com. Повторите ввод:")
        await state.update_data({"last_bot_msg_id": sent_msg.message_id})
        return

    await state.update_data({"email": message.text})

    # Новый вопрос
    sent_msg = await message.answer("Введите номер телефона (+7XXXXXXXXXX):")
    await state.update_data({"last_bot_msg_id": sent_msg.message_id})
    await state.set_state(Registration.phone)

@router.message(Registration.phone)
async def reg_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # Удаляем предыдущий вопрос
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_id)
        except:
            pass

    # Удаляем ответ пользователя
    await message.delete()

    raw_phone = re.sub(r"\D", "", message.text)
    if raw_phone.startswith("8"):
        raw_phone = "7" + raw_phone[1:]
    if len(raw_phone) == 11 and raw_phone.startswith("7"):
        phone_number = "+" + raw_phone
    else:
        sent_msg = await message.answer(
            "❌ Неверный формат номера. Используйте +7XXXXXXXXXX. Повторите ввод:"
        )
        await state.update_data({"last_bot_msg_id": sent_msg.message_id})
        return

    # Сохраняем в БД
    name = data.get("name")
    email = data.get("email")
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT OR REPLACE INTO users (tg_id, name, email, phone) VALUES (?,?,?,?)",
        (message.from_user.id, name, email, phone_number)
    )
    conn.commit()
    conn.close()

    await state.clear()

    # === ОТПРАВКА ДАННЫХ АДМИНУ ===
    # При желании выводите больше полей:
    admin_text = (
        f"Новый пользователь!\n"
        f"Имя: {name}\n"
        f"Email: {email}\n"
        f"Телефон: {phone_number}\n"
        f"tg_id: {message.from_user.id}"
    )
    await message.bot.send_message(ADMIN_ID, admin_text)

    # Предлагаем выбрать курс
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать курс", callback_data="select_course")],
        [InlineKeyboardButton(text="Изменить данные", callback_data="accept_terms")]
    ])
    await message.answer(
        "✅ Регистрация завершена! Теперь выберите курс:",
        reply_markup=kb
    )

# ---------------------------------------------
# Выбор курса: краткое описание (новое)
# ---------------------------------------------
@router.callback_query(F.data == "select_course")
async def select_course(callback: CallbackQuery):
    await callback.message.delete()

    text = (
        f"{courses_short_info['course_1']}\n\n"
        f"{courses_short_info['course_2']}\n\n"
        f"{courses_short_info['course_3']}\n\n"
        "Нажмите на нужный курс, чтобы узнать подробнее."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✨ Идеальный макияж", callback_data="course_1")],
        [InlineKeyboardButton("📋 Чек-лист косметики", callback_data="course_2")],
        [InlineKeyboardButton("🌟 Оффлайн-курс", callback_data="course_3")],
        [InlineKeyboardButton("↩️ Назад", callback_data="cancel_registration")]
    ])
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "cancel_registration")
async def cancel_registration(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Вы вернулись назад. Можете снова набрать /start или /admin.")
    await callback.answer()

# ---------------------------------------------
# Показываем полное описание выбранного курса
# ---------------------------------------------
@router.callback_query(F.data.in_(courses_full_info.keys()))
async def show_course_details(callback: CallbackQuery):
    await callback.message.delete()

    course_key = callback.data
    text = courses_full_info[course_key]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Оплатить курс 💳", callback_data=f"pay_{course_key}")],
        [InlineKeyboardButton("↩️ Назад", callback_data="select_course")]
    ])

    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()

# ---------------------------------------------
# Обработка «Оплатить курс»
# ---------------------------------------------
@router.callback_query(lambda c: c.data.startswith("pay_"))
async def pay_course(callback: CallbackQuery):
    await callback.message.delete()

    course_key = callback.data.split("_", 1)[1]
    # Берём данные из courses_data (с коротким title и числовой price)
    course_info = courses_data[course_key]

    # Достаём email/телефон из БД
    conn = sqlite3.connect("users.db")
    row = conn.execute(
        "SELECT email, phone FROM users WHERE tg_id=?",
        (callback.from_user.id,)
    ).fetchone()
    conn.close()

    user_email = "user@example.com"
    user_phone = "+70000000000"
    if row:
        user_email, user_phone = row

    # Сохраняем, какой курс выбрал пользователь (для статистики)
    conn = sqlite3.connect("users.db")
    conn.execute(
        "UPDATE users SET course=? WHERE tg_id=?",
        (course_info["title"], callback.from_user.id)
    )
    conn.commit()
    conn.close()

    # Создаём платёж
    payment_data = {
        "amount": {
            "value": str(course_info["price"]),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/testcoursee_bot"
        },
        "capture": True,
        "description": course_info["title"],

        "receipt": {
            "items": [
                {
                    "description": course_info["title"],
                    "quantity": "1.00",
                    "amount": {
                        "value": str(course_info["price"]),
                        "currency": "RUB"
                    },
                    "vat_code": str(VAT_CODE),
                    "payment_subject": "service",      # услуга
                    "payment_mode": "full_prepayment"  # полная предоплата
                }
            ],
            "phone": user_phone,
            "email": user_email,
            "tax_system_code": TAX_SYSTEM_CODE
        }
    }

    payment = Payment.create(payment_data)

    # Кнопки «Оплатить 💳» и «Назад»
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Оплатить 💳",
                url=payment.confirmation.confirmation_url
            ),
            InlineKeyboardButton(
                text="↩️ Назад",
                callback_data="select_course"
            )
        ]
    ])

    await callback.message.answer(
        "Оплатите курс по ссылке или вернитесь назад:",
        reply_markup=kb
    )

    # Если оффлайн-курс, уведомим Веронику
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
    dp.include_router(router)
