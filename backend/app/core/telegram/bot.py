#"""
#Telegram Bot class for MySaver
#Handles all bot commands and integrates with Celery tasks
#"""

import logging
from typing import Optional, Dict, Any
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from app.config import settings
from app.core.celery_app import celery_app
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Async Telegram Bot for MySaver task management
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.get("TELEGRAM_BOT_TOKEN", "")
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the bot application"""
        if not self.token:
            logger.warning("Telegram bot token not provided. Bot disabled.")
            return False
        
        try:
            self.application = Application.builder().token(self.token).build()
            
            # Register command handlers
            from app.core.telegram.handlers import (
                handle_start,
                handle_status,
                handle_report,
                handle_cancel,
                handle_list,
                handle_help,
            )
            
            self.application.add_handler(CommandHandler("start", handle_start))
            self.application.add_handler(CommandHandler("status", handle_status))
            self.application.add_handler(CommandHandler("report", handle_report))
            self.application.add_handler(CommandHandler("cancel", handle_cancel))
            self.application.add_handler(CommandHandler("list", handle_list))
            self.application.add_handler(CommandHandler("help", handle_help))
            
            # Start the application
            await self.application.initialize()
            self._initialized = True
            
            logger.info("Telegram bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            return False
    
    async def start_polling(self):
        """Start the bot in polling mode"""
        if not self._initialized:
            if not await self.initialize():
                return
        
        logger.info("Starting Telegram bot polling...")
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    async def stop(self):
        """Stop the bot"""
        if self.application and self._initialized:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self._initialized = False
            logger.info("Telegram bot stopped")
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to a chat"""
        if not self._initialized or not self.application:
            return False
        
        try:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if bot is available"""
        return self._initialized and bool(self.token)


# Global bot instance
_bot_instance: Optional[TelegramBot] = None


def get_bot() -> TelegramBot:
    """Get or create the global bot instance"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramBot()
    return _bot_instance


async def init_bot() -> TelegramBot:
    """Initialize and return the bot"""
    bot = get_bot()
    await bot.initialize()
    return bot
