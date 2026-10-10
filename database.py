# database.py
import sqlite3
import logging
from config import DATABASE_NAME, ADMIN_USER_IDS

logger = logging.getLogger(__name__)

def init_db(db_name: str = DATABASE_NAME):
    """جدول کاربران را مقداردهی اولیه کرده و ستون زبان را در صورت نیاز اضافه می‌کند."""
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
            
            # بررسی وجود ستون language برای دیتابیس‌های از قبل ساخته شده
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'language' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'fa'")
                logger.info("ستون language به جدول users افزوده شد.")
                
            conn.commit()
            logger.info("پایگاه داده با موفقیت مقداردهی اولیه شد.")
    except sqlite3.Error as e:
        logger.error(f"خطا در ایجاد پایگاه داده: {e}")

def add_user(user_id: int, username: str, first_name: str, language: str = 'fa', db_name: str = DATABASE_NAME):
    """یک کاربر جدید را به پایگاه داده اضافه یا مشخصات آن را به‌روزرسانی می‌کند."""
    if not user_id:
        return
        
    # اگر کاربر ادمین باشد، او را در دیتابیس ذخیره نکن
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
        logger.error(f"خطا در افزودن کاربر {user_id}: {e}")

def get_user_language(user_id: int, db_name: str = DATABASE_NAME) -> str | None:
    """زبان انتخاب شده کاربر را برمی‌گرداند."""
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            return None
    except sqlite3.Error as e:
        logger.error(f"خطا در خواندن زبان کاربر {user_id}: {e}")
        return None

def set_user_language(user_id: int, language: str, db_name: str = DATABASE_NAME):
    """زبان کاربر را در پایگاه داده به‌روزرسانی می‌کند."""
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"خطا در تغییر زبان کاربر {user_id}: {e}")

def get_all_user_ids(db_name: str = DATABASE_NAME) -> list[int]:
    """لیستی از تمام آیدی‌های کاربران را برای ارسال پیام همگانی برمی‌گرداند."""
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            user_ids = [item[0] for item in cursor.fetchall()]
            return user_ids
    except sqlite3.Error as e:
        logger.error(f"خطا در خواندن کاربران از پایگاه داده: {e}")
        return []