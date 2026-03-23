import sqlite3
import json
import hashlib
from typing import List, Dict, Any
import bitonic_sort


def init_db():
    """Инициализация базы данных."""
    conn = sqlite3.connect('bitonic_app.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arrays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_array TEXT NOT NULL,
            sorted_array TEXT NOT NULL,
            array_length INTEGER NOT NULL,
            sorting_time REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username: str, password: str) -> bool:
    try:
        conn = sqlite3.connect('bitonic_app.db')
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate_user(username: str, password: str) -> int:
    conn = sqlite3.connect('bitonic_app.db')
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def save_array(user_id: int, original: list, sorted_arr: list, sorting_time: float, array_length: int) -> bool:
    conn = sqlite3.connect('bitonic_app.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO arrays (user_id, original_array, sorted_array, array_length, sorting_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, json.dumps(original), json.dumps(sorted_arr), array_length, sorting_time))
    conn.commit()
    conn.close()
    return True


def get_user_arrays(user_id: int) -> List[Dict[str, Any]]:
    """🔥 ФИКС: правильно парсим JSON массивы"""
    conn = sqlite3.connect('bitonic_app.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, original_array, sorted_array, array_length, 
               sorting_time, created_at 
        FROM arrays WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    arrays = []
    for row in rows:
        try:
            # ✅ ПРАВИЛЬНО парсим JSON
            original = json.loads(row[1])
            sorted_arr = json.loads(row[2])

            # ✅ Проверяем что это списки чисел
            if isinstance(original, list) and isinstance(sorted_arr, list):
                arrays.append({
                    'id': row[0],
                    'original': original,
                    'sorted': sorted_arr,
                    'length': row[3],
                    'time': row[4],
                    'created_at': row[5]
                })
        except (json.JSONDecodeError, TypeError):
            # Пропускаем поврежденные записи
            continue
    return arrays
