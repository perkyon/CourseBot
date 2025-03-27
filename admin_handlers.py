# admin_handlers.py

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import ADMIN_ID
from database import get_all_users

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    # Пример корректной клавиатуры
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📊 Список пользователей", callback_data="admin_users_list")],
        [InlineKeyboardButton("↩️ Закрыть", callback_data="admin_close")]
    ])
    
    await message.answer("Добро пожаловать в админ-панель!", reply_markup=kb)
    
@router.callback_query(lambda c: c.data == "admin_close")
async def admin_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_users_list")
async def admin_users_list(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return
    
    users = get_all_users()
    if not users:
        await callback.message.answer("Пока нет зарегистрированных пользователей.")
        await callback.answer()
        return
    
    text = "Список пользователей:\n\n"
    for (id_, tg_id, name, email, phone, course, paid) in users:
        paid_status = "✅" if paid == 1 else "❌"
        text += (
            f"<b>ID:</b> {id_}\n"
            f"<b>tg_id:</b> {tg_id}\n"
            f"<b>Имя:</b> {name}\n"
            f"<b>Email:</b> {email}\n"
            f"<b>Телефон:</b> {phone}\n"
            f"<b>Курс:</b> {course}\n"
            f"<b>Оплачено:</b> {paid_status}\n\n"
        )
    await callback.message.answer(text)
    await callback.answer()

def register_admin_handlers(dp):
    dp.include_router(router)
