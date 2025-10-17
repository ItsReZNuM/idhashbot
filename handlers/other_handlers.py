# handlers/other_handlers.py
from utils import is_message_valid, check_rate_limit

def register_other_handlers(bot):
    @bot.message_handler(commands=['alive'])
    def alive_command(message):
        """Handles the /alive command."""
        if not is_message_valid(message):
            return
        
        user_id = message.from_user.id
        allowed, error_message = check_rate_limit(user_id)
        if not allowed:
            bot.send_message(user_id, error_message)
            return
        
        bot.send_message(
            message.chat.id,
            "I'm alive and kicking! 🤖 DigitIDBot is here!"
        )