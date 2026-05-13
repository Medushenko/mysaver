"""
Reports API endpoints for MySaver
GET /api/v1/reports/{task_id} - Get report for a task
POST /api/v1/reports/{task_id}/send - Send report to Telegram
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db_session
from app.models.task import Task
from app.schemas.report import ReportSchema, StatsSchema, LogEntrySchema, ReportResponse
from app.core.reports.generator import ReportGenerator
from app.core.telegram.notifications import send_notification

router = APIRouter()


@router.get("/reports/{task_id}", response_model=ReportResponse)
async def get_report(task_id: str):
    """
    Get detailed report for a completed task
    
    Returns statistics, logs, and metadata about the task execution.
    """
    try:
        uuid_id = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    async with get_db_session() as session:
        # Fetch task from database
        stmt = select(Task).where(Task.id == uuid_id)
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Generate report
        generator = ReportGenerator()
        report_data = await generator.generate(task, session)
        
        # Build response
        return ReportResponse(
            task_id=task_id,
            report=ReportSchema(**report_data),
            generated_at=datetime.now().isoformat()
        )


@router.post("/reports/{task_id}/send")
async def send_report_to_telegram(
    task_id: str,
    chat_id: Optional[int] = None
):
    """
    Send task report to Telegram
    
    If chat_id is not provided, sends to admin chat ID from config.
    """
    try:
        uuid_id = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    async with get_db_session() as session:
        # Fetch task from database
        stmt = select(Task).where(Task.id == uuid_id)
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Generate report
        generator = ReportGenerator()
        report_data = await generator.generate(task, session)
        
        # Format as text for Telegram
        report_text = generator.format_text(report_data)
        
        # Determine chat ID
        if chat_id is None:
            from app.config import settings
            admin_chat_id = settings.get("ADMIN_CHAT_ID")
            if not admin_chat_id:
                raise HTTPException(
                    status_code=400,
                    detail="No chat_id provided and ADMIN_CHAT_ID not configured"
                )
            # Use first admin ID if multiple are configured
            chat_id = int(admin_chat_id.split(",")[0])
        
        # Send notification
        success = await send_notification(chat_id, report_text)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to send report to Telegram"
            )
        
        return {
            "task_id": task_id,
            "sent_to": chat_id,
            "status": "sent"
        }
