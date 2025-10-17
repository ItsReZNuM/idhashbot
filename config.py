# config.py
import os
from dotenv import load_dotenv

# بارگذاری متغیرها از فایل .env
load_dotenv()

# توکن ربات تلگرام
TOKEN = os.getenv('TOKEN')

# لیست آیدی عددی ادمین‌ها (با کاما جدا شوند)
# مثال: ADMIN_USER_IDS=12345,67890
ADMIN_IDS_STR = os.getenv('ADMIN_USER_IDS', '')
ADMIN_USER_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

# نام فایل پایگاه داده
DATABASE_NAME = "users.db"