import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "db.sqlite3"

def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """初期化：テーブル作成"""
    conn = get_connection()
    cur = conn.cursor()

    # ユーザー情報
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL
    );
    """)

    # クッキー情報
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cookies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        cookie_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    conn.commit()
    conn.close()


def get_user_id(username: str):
    """ユーザー名からユーザーIDを取得（なければ作成）"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
    else:
        cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        user_id = cur.lastrowid

    conn.close()
    return user_id


def save_cookies_to_db(username: str, cookie_dict: list):
    """クッキーをDBに保存"""
    user_id = get_user_id(username)
    conn = get_connection()
    cur = conn.cursor()

    cookie_json = json.dumps(cookie_dict, ensure_ascii=False)
    cur.execute("INSERT INTO cookies (user_id, cookie_data) VALUES (?, ?)", (user_id, cookie_json))
    conn.commit()
    conn.close()
    print("DBにクッキーを保存しました")


def get_latest_cookies(username: str):
    """最新のクッキーをDBから取得"""
    user_id = get_user_id(username)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT cookie_data FROM cookies
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    return None
