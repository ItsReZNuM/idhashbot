# database.py
import sqlite3
import logging
from config import DATABASE_NAME, ADMIN_USER_IDS

logger = logging.getLogger(__name__)


def init_db(db_name: str = DATABASE_NAME):
    """Initialize database and migrate language column if missing."""
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    language TEXT DEFAULT 'fa'
                )
            """)

            # Ensure language column exists for existing legacy databases
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'language' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'fa'")
                logger.info("Migrated database: added 'language' column to users table.")

            conn.commit()
            logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")


def add_user(user_id: int, username: str, first_name: str, language: str = 'fa', db_name: str = DATABASE_NAME):
    """Add a new user or update existing user info in the database."""
    if not user_id:
        return

    # Do not save admin IDs to the regular broadcast users table
    if user_id in ADMIN_USER_IDS:
        return

    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, language)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name
            """, (user_id, username if username else "", first_name if first_name else "", language))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error adding/updating user {user_id}: {e}")


def get_user_language(user_id: int, db_name: str = DATABASE_NAME) -> str | None:
    """Retrieve saved language preference for a user."""
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            return None
    except sqlite3.Error as e:
        logger.error(f"Error getting language for user {user_id}: {e}")
        return None


def set_user_language(user_id: int, language: str, db_name: str = DATABASE_NAME):
    """Update user language preference."""
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error updating language for user {user_id}: {e}")


def get_all_user_ids(db_name: str = DATABASE_NAME) -> list[int]:
    """Retrieve all user IDs for broadcast messages."""
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            user_ids = [item[0] for item in cursor.fetchall()]
            return user_ids
    except sqlite3.Error as e:
        logger.error(f"Error fetching user IDs from database: {e}")
        return []