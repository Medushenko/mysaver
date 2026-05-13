"""
Telegram Bot Command Handlers for MySaver
Handles /start, /status, /report, /cancel, /list, /help commands
"""
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from app.models.task import Task, TaskStatus
from app.db import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - welcome message and instructions"""
    welcome_text = (
        "👋 <b>Добро пожаловать в MySaver!</b>\n\n"
        "Я ваш помощник для управления задачами копирования файлов между облачными хранилищами.\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Показать это сообщение\n"
        "/status [task_id] - Узнать статус задачи\n"
        "/report [task_id] - Получить отчёт о завершённой задаче\n"
        "/cancel [task_id] - Отменить задачу\n"
        "/list - Показать все активные задачи\n"
        "/help - Подробная справка\n\n"
        "Для получения статуса или отчёта укажите ID задачи:\n"
        "<code>/status 550e8400-e29b-41d4-a716-446655440000</code>"
    )
    
    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show task status"""
    task_id = _extract_task_id(context.args)
    
    if not task_id:
        await update.message.reply_text(
            "❌ Пожалуйста, укажите ID задачи:\n"
            "<code>/status 550e8400-e29b-41d4-a716-446655440000</code>",
            parse_mode="HTML"
        )
        return
    
    try:
        async with get_db_session() as session:
            task = await _get_task_by_id(session, task_id)
            
            if not task:
                await update.message.reply_text(f"❌ Задача {task_id} не найдена")
                return
            
            status_emoji = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.RUNNING: "🔄",
                TaskStatus.SUCCESS: "✅",
                TaskStatus.PARTIAL: "⚠️",
                TaskStatus.FAILED: "❌",
            }.get(task.status, "❓")
            
            progress = ""
            if task.bytes_planned > 0:
                percent = int((task.bytes_done / task.bytes_planned) * 100)
                progress = f"\n📊 Прогресс: {percent}% ({_format_size(task.bytes_done)} / {_format_size(task.bytes_planned)})"
            
            status_text = (
                f"{status_emoji} <b>Статус задачи</b>\n\n"
                f"<b>ID:</b> <code>{task.id}</code>\n"
                f"<b>Статус:</b> {task.status.value}\n"
                f"<b>Источник:</b> {task.source_provider}:{task.source_path}\n"
                f"<b>Назначение:</b> {task.dest_provider}:{task.dest_path}\n"
                f"{progress}"
            )
            
            if task.error_reason:
                status_text += f"\n\n<b>Ошибка:</b> {task.error_reason}"
            
            if task.created_at:
                status_text += f"\n<b>Создана:</b> {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            
            if task.completed_at:
                status_text += f"\n<b>Завершена:</b> {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
            
            await update.message.reply_text(status_text, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        await update.message.reply_text(f"❌ Ошибка при получении статуса: {str(e)}")


async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command - show task report"""
    task_id = _extract_task_id(context.args)
    
    if not task_id:
        await update.message.reply_text(
            "❌ Пожалуйста, укажите ID задачи:\n"
            "<code>/report 550e8400-e29b-41d4-a716-446655440000</code>",
            parse_mode="HTML"
        )
        return
    
    try:
        async with get_db_session() as session:
            task = await _get_task_by_id(session, task_id)
            
            if not task:
                await update.message.reply_text(f"❌ Задача {task_id} не найдена")
                return
            
            if task.status not in [TaskStatus.SUCCESS, TaskStatus.PARTIAL, TaskStatus.FAILED]:
                await update.message.reply_text(
                    f"⏳ Задача ещё не завершена. Текущий статус: {task.status.value}"
                )
                return
            
            # Generate report
            duration = ""
            if task.started_at and task.completed_at:
                delta = task.completed_at - task.started_at
                duration = f"\n<b>Время выполнения:</b> {_format_duration(delta.total_seconds())}"
            
            speed = ""
            if task.started_at and task.completed_at and task.bytes_done > 0:
                delta_seconds = (task.completed_at - task.started_at).total_seconds()
                if delta_seconds > 0:
                    speed_mb = (task.bytes_done / delta_seconds) / (1024 * 1024)
                    speed = f"\n<b>Скорость:</b> {speed_mb:.2f} MB/s"
            
            report_text = (
                f"📊 <b>Отчёт о задаче</b>\n\n"
                f"<b>ID:</b> <code>{task.id}</code>\n"
                f"<b>Статус:</b> {task.status.value}\n"
                f"<b>Источник:</b> {task.source_provider}:{task.source_path}\n"
                f"<b>Назначение:</b> {task.dest_provider}:{task.dest_path}\n\n"
                f"<b>Всего файлов:</b> {_format_size(task.bytes_planned)}\n"
                f"<b>Скопировано:</b> {_format_size(task.bytes_done)}\n"
                f"{duration}{speed}"
            )
            
            if task.error_reason:
                report_text += f"\n\n<b>Ошибки:</b>\n{task.error_reason}"
            
            await update.message.reply_text(report_text, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await update.message.reply_text(f"❌ Ошибка при生成 отчёта: {str(e)}")


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command - cancel a task"""
    task_id = _extract_task_id(context.args)
    
    if not task_id:
        await update.message.reply_text(
            "❌ Пожалуйста, укажите ID задачи:\n"
            "<code>/cancel 550e8400-e29b-41d4-a716-446655440000</code>",
            parse_mode="HTML"
        )
        return
    
    try:
        async with get_db_session() as session:
            task = await _get_task_by_id(session, task_id)
            
            if not task:
                await update.message.reply_text(f"❌ Задача {task_id} не найдена")
                return
            
            if task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.PARTIAL]:
                await update.message.reply_text(
                    f"⚠️ Задача уже завершена со статусом: {task.status.value}"
                )
                return
            
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.FAILED
                task.error_reason = "Cancelled by user via Telegram"
                await session.commit()
                await update.message.reply_text(f"✅ Задача {task_id} отменена")
                return
            
            # For running tasks, trigger Celery task to cancel
            from app.core.tasks import cancel_task
            cancel_task.delay(str(task_id))
            
            await update.message.reply_text(
                f"🔄 Запрос на отмену задачи {task_id} отправлен. "
                "Задача будет остановлена в ближайшее время."
            )
            
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        await update.message.reply_text(f"❌ Ошибка при отмене задачи: {str(e)}")


async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command - show all active tasks"""
    try:
        async with get_db_session() as session:
            # Get user's active tasks (in real app, filter by user_id from context)
            stmt = select(Task).where(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
            ).limit(10)
            
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            
            if not tasks:
                await update.message.reply_text("📭 Нет активных задач")
                return
            
            list_text = "📋 <b>Активные задачи</b>\n\n"
            
            for task in tasks:
                status_emoji = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.RUNNING: "🔄",
                }.get(task.status, "❓")
                
                progress = ""
                if task.bytes_planned > 0:
                    percent = int((task.bytes_done / task.bytes_planned) * 100)
                    progress = f" ({percent}%)"
                
                list_text += (
                    f"{status_emoji} <code>{task.id}</code>{progress}\n"
                    f"   {task.source_provider} → {task.dest_provider}\n"
                )
            
            await update.message.reply_text(list_text, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        await update.message.reply_text(f"❌ Ошибка при получении списка задач: {str(e)}")


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - detailed help"""
    help_text = (
        "📖 <b>Справка по MySaver</b>\n\n"
        "<b>Как создать задачу?</b>\n"
        "Используйте веб-интерфейс или API для создания задач копирования.\n\n"
        "<b>Как узнать статус?</b>\n"
        "<code>/status &lt;task_id&gt;</code>\n\n"
        "<b>Как получить отчёт?</b>\n"
        "<code>/report &lt;task_id&gt;</code>\n"
        "Отчёт доступен только для завершённых задач.\n\n"
        "<b>Как отменить задачу?</b>\n"
        "<code>/cancel &lt;task_id&gt;</code>\n"
        "Можно отменить только задачи со статусом pending или running.\n\n"
        "<b>Политики обработки конфликтов:</b>\n"
        "• SKIP — пропустить существующие файлы\n"
        "• OVERWRITE — перезаписать существующие файлы\n"
        "• KEEP_BOTH — сохранить оба файла (переименовать новый)\n"
        "• RENAME — переименовать новый файл\n\n"
        "<b>Поддержка:</b>\n"
        "При возникновении проблем обратитесь к администратору."
    )
    
    await update.message.reply_text(help_text, parse_mode="HTML")


def _extract_task_id(args: list) -> Optional[str]:
    """Extract task ID from command arguments"""
    if not args:
        return None
    return args[0]


async def _get_task_by_id(session: AsyncSession, task_id: str) -> Optional[Task]:
    """Get task by ID"""
    try:
        uuid_id = UUID(task_id)
    except ValueError:
        return None
    
    stmt = select(Task).where(Task.id == uuid_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _format_size(bytes_value: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"


def _format_duration(seconds: float) -> str:
    """Format seconds to human-readable duration"""
    if seconds < 60:
        return f"<b>Время выполнения:</b> {seconds:.1f} сек"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"<b>Время выполнения:</b> {minutes:.1f} мин"
    else:
        hours = seconds / 3600
        return f"<b>Время выполнения:</b> {hours:.1f} ч"
