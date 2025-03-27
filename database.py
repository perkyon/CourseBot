# database.py

import sqlite3
from config import DB_PATH

def init_db():
    """Создаёт таблицы, если ещё не созданы."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            name TEXT,
            email TEXT,
            phone TEXT,
            course TEXT,
            paid INTEGER DEFAULT 0
        )
    ''')

    # Таблица для хранения сообщений от пользователей (если нужна)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_tg_id INTEGER,
            message_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def get_all_users():
    """Возвращает список кортежей (id, tg_id, name, email, phone, course, paid)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT id, tg_id, name, email, phone, course, paid FROM users"
    ).fetchall()
    conn.close()
    return rows

def insert_user_message(user_tg_id, text):
    """Сохраняет входящее сообщение в таблицу messages."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_tg_id, message_text) VALUES (?, ?)",
        (user_tg_id, text)
    )
    conn.commit()
    conn.close()
