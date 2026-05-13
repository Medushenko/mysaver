"""
Telegram package initialization
"""
from app.core.telegram.bot import TelegramBot, get_bot, init_bot

__all__ = [
    'TelegramBot',
    'get_bot',
    'init_bot',
]
