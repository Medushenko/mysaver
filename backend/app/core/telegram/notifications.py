"""
Telegram Notifications for MySaver
Send task status updates and notifications to users
"""
import logging
from typing import Optional, List
from telegram import Bot
from app.core.telegram.bot import get_bot
from app.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


async def send_notification(
    chat_id: int,
    message: str,
    parse_mode: str = "HTML"
) -> bool:
    """
    Send a notification message to a user
    
    Args:
        chat_id: Telegram chat ID of the user
        message: Message text (supports HTML formatting)
        parse_mode: Parse mode for the message (HTML or Markdown)
    
    Returns:
        True if message was sent successfully, False otherwise
    """
    bot = get_bot()
    
    if not bot.is_available():
        logger.warning(f"Telegram bot not available, skipping notification to {chat_id}")
        return False
    
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode=parse_mode)
        logger.info(f"Notification sent to {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification to {chat_id}: {e}")
        return False


async def send_task_status(
    chat_id: int,
    task: Task,
    custom_message: Optional[str] = None
) -> bool:
    """
    Send task status update to a user
    
    Args:
        chat_id: Telegram chat ID of the user
        task: Task object
        custom_message: Optional custom message to prepend
    
    Returns:
        True if message was sent successfully, False otherwise
    """
    status_emoji = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.RUNNING: "🔄",
        TaskStatus.SUCCESS: "✅",
        TaskStatus.PARTIAL: "⚠️",
        TaskStatus.FAILED: "❌",
    }.get(task.status, "❓")
    
    # Build status message
    progress = ""
    if task.bytes_planned > 0:
        percent = int((task.bytes_done / task.bytes_planned) * 100)
        progress_bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
        progress = (
            f"\n\n📊 Прогресс: {percent}%\n"
            f"[{progress_bar}]\n"
            f"{_format_size(task.bytes_done)} / {_format_size(task.bytes_planned)}"
        )
    
    message = custom_message or f"{status_emoji} <b>Обновление статуса задачи</b>"
    message += (
        f"\n\n<b>ID:</b> <code>{task.id}</code>\n"
        f"<b>Статус:</b> {task.status.value}\n"
        f"<b>Источник:</b> {task.source_provider}:{task.source_path}\n"
        f"<b>Назначение:</b> {task.dest_provider}:{task.dest_path}"
        f"{progress}"
    )
    
    if task.error_reason:
        message += f"\n\n<b>Ошибка:</b> {task.error_reason}"
    
    return await send_notification(chat_id, message)


async def send_task_started(chat_id: int, task: Task) -> bool:
    """Send notification that task has started"""
    return await send_task_status(
        chat_id,
        task,
        "🚀 <b>Задача запущена!</b>"
    )


async def send_task_completed(chat_id: int, task: Task) -> bool:
    """Send notification that task has completed"""
    duration = ""
    if task.started_at and task.completed_at:
        delta = (task.completed_at - task.started_at).total_seconds()
        if delta < 60:
            duration = f"\n⏱️ Время: {delta:.1f} сек"
        elif delta < 3600:
            duration = f"\n⏱️ Время: {delta/60:.1f} мин"
        else:
            duration = f"\n⏱️ Время: {delta/3600:.1f} ч"
    
    return await send_task_status(
        chat_id,
        task,
        f"✅ <b>Задача завершена!</b>{duration}"
    )


async def send_task_failed(chat_id: int, task: Task) -> bool:
    """Send notification that task has failed"""
    return await send_task_status(
        chat_id,
        task,
        "❌ <b>Задача не выполнена!</b>"
    )


async def send_progress_update(
    chat_id: int,
    task: Task,
    percent: int
) -> bool:
    """
    Send progress update notification
    
    Args:
        chat_id: Telegram chat ID
        task: Task object
        percent: Progress percentage (0-100)
    """
    progress_bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
    
    message = (
        f"🔄 <b>Прогресс выполнения</b>\n\n"
        f"<b>ID:</b> <code>{task.id}</code>\n"
        f"[{progress_bar}] {percent}%\n"
        f"{_format_size(task.bytes_done)} / {_format_size(task.bytes_planned)}"
    )
    
    return await send_notification(chat_id, message)


def _format_size(bytes_value: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"


async def broadcast_to_admins(message: str) -> List[int]:
    """
    Broadcast message to all admin chat IDs
    
    Args:
        message: Message to broadcast
    
    Returns:
        List of chat IDs where message was sent successfully
    """
    from app.config import settings
    
    admin_ids = []
    admin_chat_id = settings.get("ADMIN_CHAT_ID")
    
    if admin_chat_id:
        # Support multiple comma-separated IDs
        admin_ids = [id.strip() for id in admin_chat_id.split(",")]
    
    successful = []
    for chat_id_str in admin_ids:
        try:
            chat_id = int(chat_id_str)
            if await send_notification(chat_id, message):
                successful.append(chat_id)
        except ValueError:
            logger.warning(f"Invalid admin chat ID: {chat_id_str}")
    
    return successful
