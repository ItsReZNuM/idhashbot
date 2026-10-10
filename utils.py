# utils.py
import time
import logging

logger = logging.getLogger(__name__)

# زمان راه‌اندازی ربات بر حسب ثانیه (Unix Timestamp) برای نادیده گرفتن پیام‌های ارسال شده قبل از اجرای ربات
bot_start_time = time.time()

# دیکشنری نگهداری نرخ ارسال پیام کاربران در حافظه
message_tracker = {}


def is_message_valid(message) -> bool:
    """بررسی می‌کند که آیا پیام ارسالی بعد از زمان روشن شدن ربات است یا خیر."""
    if not message or not hasattr(message, 'date') or not message.date:
        return True
    message_time = message.date
    if message_time < bot_start_time:
        logger.warning(f"نادیده گرفتن پیام قدیمی از کاربر {getattr(message.chat, 'id', 'unknown')}")
        return False
    return True


def check_rate_limit(user_id: int) -> tuple[bool, int]:
    """
    بررسی محدودیت نرخ ارسال پیام.
    خروجی: (مجاز بودن پیام، ثانیه‌های باقیمانده از محدودیت)
    """
    current_time = time.time()

    if user_id not in message_tracker:
        message_tracker[user_id] = {'count': 0, 'last_time': current_time, 'temp_block_until': 0}

    tracker = message_tracker[user_id]

    if current_time < tracker['temp_block_until']:
        remaining = int(tracker['temp_block_until'] - current_time)
        return False, remaining

    if current_time - tracker['last_time'] > 1.0:
        tracker['count'] = 0
        tracker['last_time'] = current_time

    tracker['count'] += 1

    if tracker['count'] > 3:
        tracker['temp_block_until'] = current_time + 30
        return False, 30

    return True, 0