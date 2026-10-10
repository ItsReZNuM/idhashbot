# config.py
import os
import re
from dotenv import load_dotenv

# بارگذاری متغیرها از فایل .env
load_dotenv()

# توکن ربات تلگرام
TOKEN = os.getenv('TOKEN', '').strip()

# لیست آیدی عددی ادمین‌ها (پشتیبانی از فرمت‌های کاما، لیست یا تک‌آیدی)
ADMIN_IDS_RAW = os.getenv('ADMIN_USER_IDS', '')
ADMIN_USER_IDS = [int(admin_id) for admin_id in re.findall(r'\d+', ADMIN_IDS_RAW)]

# نام فایل پایگاه داده
DATABASE_NAME = os.getenv('DATABASE_NAME', 'users.db')