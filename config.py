# config.py
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv('TOKEN', '').strip()

# List of admin user IDs (supports comma-separated values, lists, or single ID)
ADMIN_IDS_RAW = os.getenv('ADMIN_USER_IDS', '')
ADMIN_USER_IDS = [int(admin_id) for admin_id in re.findall(r'\d+', ADMIN_IDS_RAW)]

# Database file name
DATABASE_NAME = os.getenv('DATABASE_NAME', 'users.db')