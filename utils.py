# utils.py
import time
import logging

logger = logging.getLogger(__name__)

# Bot startup timestamp in seconds (Unix Timestamp) to ignore stale messages received before start
bot_start_time = time.time()

# In-memory message tracker for rate limiting
message_tracker = {}


def is_message_valid(message) -> bool:
    """Check if message was sent after bot startup."""
    if not message or not hasattr(message, 'date') or not message.date:
        return True
    message_time = message.date
    if message_time < bot_start_time:
        logger.warning(f"Ignoring stale message from user {getattr(message.chat, 'id', 'unknown')}")
        return False
    return True


def check_rate_limit(user_id: int) -> tuple[bool, int]:
    """
    Check rate limiting for user.
    Returns: (is_allowed: bool, remaining_seconds: int)
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