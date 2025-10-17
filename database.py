# database.py
import sqlite3
import logging

from config import DATABASE_NAME

logger = logging.getLogger(__name__)

def init_db():
    """جدول کاربران را در پایگاه داده ایجاد می‌کند (اگر وجود نداشته باشد)."""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT
                )
            """)
            conn.commit()
            logger.info("پایگاه داده با موفقیت مقداردهی اولیه شد.")
    except sqlite3.Error as e:
        logger.error(f"خطا در ایجاد پایگاه داده: {e}")

def add_user(user_id: int, username: str, first_name: str):
    """یک کاربر جدید را به پایگاه داده اضافه می‌کند. اگر کاربر از قبل وجود داشته باشد، کاری انجام نمی‌دهد."""
    if not user_id:
        return
        
    # اگر کاربر ادمین باشد، او را در دیتابیس ذخیره نکن
    from config import ADMIN_USER_IDS
    if user_id in ADMIN_USER_IDS:
        return

    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # از INSERT OR IGNORE استفاده می‌کنیم تا در صورت وجود کاربر، خطایی رخ ندهد
            cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            """, (user_id, username if username else "ندارد", first_name))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"کاربر جدید ذخیره شد: {user_id} - {first_name}")
    except sqlite3.Error as e:
        logger.error(f"خطا در افزودن کاربر {user_id}: {e}")

def get_all_user_ids():
    """لیستی از تمام آیدی‌های کاربران را برای ارسال پیام همگانی برمی‌گرداند."""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            # نتیجه به صورت لیستی از تاپل‌هاست، آن را به لیست آیدی تبدیل می‌کنیم
            user_ids = [item[0] for item in cursor.fetchall()]
            return user_ids
    except sqlite3.Error as e:
        logger.error(f"خطا در خواندن کاربران از پایگاه داده: {e}")
        return []