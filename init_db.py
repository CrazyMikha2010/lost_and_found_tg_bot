import sqlite3

# this code initialises sqlite database

def init_db():
    conn = sqlite3.connect("path/to/your/database.db")
    cursor = conn.cursor()
    """table for storing
            category for filtering
            message_id (to forward it)
            date for filtering"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS found_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            message_id TEXT NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    """table for storing
            user_id for tracking subscriptions
            category to know which they are following"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            PRIMARY KEY (user_id, category)
        )
    ''')
    """table for storing
            all user ids for sendall func
            their time of registration"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
