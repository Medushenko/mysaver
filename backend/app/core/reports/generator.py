"""
Report Generator for MySaver
Generates detailed reports for completed tasks
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from app.models.task import Task, TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Single log entry in the report"""
    timestamp: str
    action: str  # 'copied', 'skipped', 'error', 'renamed'
    source_path: str
    dest_path: str
    size: int
    message: Optional[str] = None


@dataclass 
class ReportStats:
    """Statistics for the report"""
    total_files: int = 0
    total_folders: int = 0
    total_size: int = 0
    copied_files: int = 0
    copied_size: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    renamed_files: int = 0
    duration_seconds: float = 0.0
    speed_mb_per_sec: float = 0.0


class ReportGenerator:
    """
    Generate detailed reports for completed tasks
    """
    
    def __init__(self):
        self.logs: List[LogEntry] = []
    
    async def generate(self, task: Task, session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Generate a complete report for a task
        
        Args:
            task: Task object
            session: Optional DB session for additional data
        
        Returns:
            Dictionary with report data matching ReportSchema
        """
        # Calculate statistics
        stats = await self._calculate_stats(task)
        
        # Get logs (in real implementation, fetch from DB or log storage)
        logs = await self._get_logs(task)
        
        # Build report
        report = {
            "task_id": str(task.id),
            "status": task.status.value if isinstance(task.status, TaskStatus) else task.status,
            "stats": {
                "total_files": stats.total_files,
                "total_folders": stats.total_folders,
                "total_size": stats.total_size,
                "copied_files": stats.copied_files,
                "copied_size": stats.copied_size,
                "skipped_files": stats.skipped_files,
                "failed_files": stats.failed_files,
                "renamed_files": stats.renamed_files,
                "duration_seconds": stats.duration_seconds,
                "speed_mb_per_sec": stats.speed_mb_per_sec,
            },
            "logs": [self._log_to_dict(log) for log in logs],
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "source_provider": task.source_provider,
            "source_path": task.source_path,
            "dest_provider": task.dest_provider,
            "dest_path": task.dest_path,
            "error_reason": task.error_reason,
            "conflict_policy": task.conflict_policy.value if task.conflict_policy else None,
        }
        
        return report
    
    async def _calculate_stats(self, task: Task) -> ReportStats:
        """Calculate statistics for the task"""
        stats = ReportStats()
        
        # Basic stats from task
        stats.total_size = task.bytes_planned
        stats.copied_size = task.bytes_done
        
        # Estimate file counts (in real implementation, get from detailed logs)
        # This is a simplified estimation
        avg_file_size = 1024 * 1024  # 1MB average
        if avg_file_size > 0:
            stats.total_files = max(1, task.bytes_planned // avg_file_size)
            stats.copied_files = max(1, task.bytes_done // avg_file_size)
        
        # Calculate duration and speed
        if task.started_at and task.completed_at:
            delta = (task.completed_at - task.started_at).total_seconds()
            stats.duration_seconds = delta
            
            if delta > 0 and task.bytes_done > 0:
                stats.speed_mb_per_sec = (task.bytes_done / delta) / (1024 * 1024)
        
        # Estimate other counts based on conflict policy
        if task.conflict_policy:
            # These would be populated from actual operation logs
            pass
        
        return stats
    
    async def _get_logs(self, task: Task) -> List[LogEntry]:
        """
        Get operation logs for the task
        
        In a real implementation, this would fetch from a logs table or file storage.
        For now, we create synthetic logs based on task status.
        """
        logs = []
        
        # Add start log
        if task.started_at:
            logs.append(LogEntry(
                timestamp=task.started_at.isoformat(),
                action="started",
                source_path=task.source_path,
                dest_path=task.dest_path,
                size=0,
                message=f"Task started: {task.source_provider} → {task.dest_provider}"
            ))
        
        # Add completion log
        if task.completed_at:
            action = "completed" if task.status == TaskStatus.SUCCESS else "failed"
            message = f"Task {task.status.value}"
            
            if task.error_reason:
                message += f": {task.error_reason}"
            
            logs.append(LogEntry(
                timestamp=task.completed_at.isoformat(),
                action=action,
                source_path=task.source_path,
                dest_path=task.dest_path,
                size=task.bytes_done,
                message=message
            ))
        
        return logs
    
    def _log_to_dict(self, log: LogEntry) -> Dict[str, Any]:
        """Convert LogEntry to dictionary"""
        return {
            "timestamp": log.timestamp,
            "action": log.action,
            "source_path": log.source_path,
            "dest_path": log.dest_path,
            "size": log.size,
            "message": log.message,
        }
    
    def format_text(self, report: Dict[str, Any]) -> str:
        """Format report as plain text (for Telegram)"""
        from app.core.reports.formatters import format_report_text
        return format_report_text(report)
    
    def format_html(self, report: Dict[str, Any]) -> str:
        """Format report as HTML (for web)"""
        from app.core.reports.formatters import format_report_html
        return format_report_html(report)
