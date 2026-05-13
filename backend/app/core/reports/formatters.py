"""
Report Formatters for MySaver
Format reports as text (for Telegram) or HTML (for web)
"""
from typing import Dict, Any, List


def format_report_text(report: Dict[str, Any]) -> str:
    """
    Format report as plain text suitable for Telegram
    
    Args:
        report: Report dictionary from ReportGenerator
        
    Returns:
        Formatted text string
    """
    stats = report.get("stats", {})
    
    # Header
    status_emoji = {
        "success": "✅",
        "partial": "⚠️",
        "failed": "❌",
        "pending": "⏳",
        "running": "🔄",
    }.get(report.get("status", ""), "❓")
    
    lines = [
        f"{status_emoji} ОТЧЁТ О ЗАДАЧЕ",
        "",
        f"ID задачи: {report.get('task_id')}",
        f"Статус: {report.get('status')}",
        "",
        "=== ИСТОЧНИК ===",
        f"Провайдер: {report.get('source_provider')}",
        f"Путь: {report.get('source_path')}",
        "",
        "=== НАЗНАЧЕНИЕ ===",
        f"Провайдер: {report.get('dest_provider')}",
        f"Путь: {report.get('dest_path')}",
        "",
        "=== СТАТИСТИКА ===",
        f"Всего файлов: {stats.get('total_files', 0)}",
        f"Всего папок: {stats.get('total_folders', 0)}",
        f"Общий размер: {_format_size(stats.get('total_size', 0))}",
        "",
        f"Скопировано файлов: {stats.get('copied_files', 0)}",
        f"Скопировано размера: {_format_size(stats.get('copied_size', 0))}",
        f"Пропущено файлов: {stats.get('skipped_files', 0)}",
        f"Не удалось скопировать: {stats.get('failed_files', 0)}",
        f"Переименовано файлов: {stats.get('renamed_files', 0)}",
        "",
    ]
    
    # Duration and speed
    duration = stats.get('duration_seconds', 0)
    if duration > 0:
        if duration < 60:
            lines.append(f"Время выполнения: {duration:.1f} сек")
        elif duration < 3600:
            lines.append(f"Время выполнения: {duration/60:.1f} мин")
        else:
            lines.append(f"Время выполнения: {duration/3600:.1f} ч")
    
    speed = stats.get('speed_mb_per_sec', 0)
    if speed > 0:
        lines.append(f"Скорость: {speed:.2f} MB/s")
    
    lines.append("")
    
    # Timestamps
    if report.get('created_at'):
        lines.append(f"Создана: {report['created_at']}")
    if report.get('started_at'):
        lines.append(f"Запущена: {report['started_at']}")
    if report.get('completed_at'):
        lines.append(f"Завершена: {report['completed_at']}")
    
    # Error reason
    if report.get('error_reason'):
        lines.append("")
        lines.append("=== ОШИБКИ ===")
        lines.append(report['error_reason'])
    
    # Conflict policy
    if report.get('conflict_policy'):
        lines.append("")
        lines.append(f"Политика конфликтов: {report['conflict_policy']}")
    
    # Logs (limit to last 10)
    logs = report.get('logs', [])
    if logs:
        lines.append("")
        lines.append("=== ПОСЛЕДНИЕ ОПЕРАЦИИ ===")
        for log in logs[-10:]:
            action_emoji = {
                "started": "🚀",
                "completed": "✅",
                "failed": "❌",
                "copied": "📄",
                "skipped": "⏭️",
                "renamed": "✏️",
                "error": "⚠️",
            }.get(log.get('action', ''), '•')
            
            lines.append(
                f"{action_emoji} [{log.get('timestamp', '')}] "
                f"{log.get('action', '')}: {log.get('message', '')}"
            )
    
    return "\n".join(lines)


def format_report_html(report: Dict[str, Any]) -> str:
    """
    Format report as HTML suitable for web display
    
    Args:
        report: Report dictionary from ReportGenerator
        
    Returns:
        Formatted HTML string
    """
    stats = report.get("stats", {})
    
    status_class = {
        "success": "success",
        "partial": "warning",
        "failed": "danger",
        "pending": "info",
        "running": "primary",
    }.get(report.get("status", ""), "secondary")
    
    html_parts = [
        f'<div class="report report-{status_class}">',
        f'  <h2>Отчёт о задаче: {report.get("task_id")}</h2>',
        f'  <p><strong>Статус:</strong> <span class="badge badge-{status_class}">{report.get("status")}</span></p>',
        '',
        '  <h3>Источник</h3>',
        '  <ul>',
        f'    <li><strong>Провайдер:</strong> {report.get("source_provider")}</li>',
        f'    <li><strong>Путь:</strong> <code>{report.get("source_path")}</code></li>',
        '  </ul>',
        '',
        '  <h3>Назначение</h3>',
        '  <ul>',
        f'    <li><strong>Провайдер:</strong> {report.get("dest_provider")}</li>',
        f'    <li><strong>Путь:</strong> <code>{report.get("dest_path")}</code></li>',
        '  </ul>',
        '',
        '  <h3>Статистика</h3>',
        '  <table class="table table-striped">',
        '    <tbody>',
        f'      <tr><td>Всего файлов</td><td>{stats.get("total_files", 0)}</td></tr>',
        f'      <tr><td>Всего папок</td><td>{stats.get("total_folders", 0)}</td></tr>',
        f'      <tr><td>Общий размер</td><td>{_format_size(stats.get("total_size", 0))}</td></tr>',
        f'      <tr><td>Скопировано файлов</td><td>{stats.get("copied_files", 0)}</td></tr>',
        f'      <tr><td>Скопировано размера</td><td>{_format_size(stats.get("copied_size", 0))}</td></tr>',
        f'      <tr><td>Пропущено файлов</td><td>{stats.get("skipped_files", 0)}</td></tr>',
        f'      <tr><td>Не удалось скопировать</td><td>{stats.get("failed_files", 0)}</td></tr>',
        f'      <tr><td>Переименовано файлов</td><td>{stats.get("renamed_files", 0)}</td></tr>',
    ]
    
    # Duration and speed
    duration = stats.get('duration_seconds', 0)
    speed = stats.get('speed_mb_per_sec', 0)
    
    if duration > 0:
        duration_formatted = _format_duration(duration)
        html_parts.append(f'      <tr><td>Время выполнения</td><td>{duration_formatted}</td></tr>')
    
    if speed > 0:
        html_parts.append(f'      <tr><td>Скорость</td><td>{speed:.2f} MB/s</td></tr>')
    
    html_parts.extend([
        '    </tbody>',
        '  </table>',
        '',
        '  <h3>Временные метки</h3>',
        '  <ul>',
    ])
    
    if report.get('created_at'):
        html_parts.append(f'    <li><strong>Создана:</strong> {report["created_at"]}</li>')
    if report.get('started_at'):
        html_parts.append(f'    <li><strong>Запущена:</strong> {report["started_at"]}</li>')
    if report.get('completed_at'):
        html_parts.append(f'    <li><strong>Завершена:</strong> {report["completed_at"]}</li>')
    
    html_parts.append('  </ul>')
    
    # Error reason
    if report.get('error_reason'):
        html_parts.extend([
            '',
            '  <h3 class="text-danger">Ошибки</h3>',
            f'  <div class="alert alert-danger">{report["error_reason"]}</div>',
        ])
    
    # Conflict policy
    if report.get('conflict_policy'):
        html_parts.append(
            f'  <p><strong>Политика конфликтов:</strong> {report["conflict_policy"]}</p>'
        )
    
    # Logs
    logs = report.get('logs', [])
    if logs:
        html_parts.extend([
            '',
            '  <h3>Журнал операций</h3>',
            '  <div class="log-container">',
            '    <ul class="log-list">',
        ])
        
        for log in logs[-20:]:  # Limit to last 20
            html_parts.append(
                f'      <li class="log-entry log-{log.get("action", "")}">'
                f'<span class="log-timestamp">{log.get("timestamp", "")}</span> '
                f'<span class="log-action">{log.get("action", "")}</span>: '
                f'{log.get("message", "")}'
                f'</li>'
            )
        
        html_parts.extend([
            '    </ul>',
            '  </div>',
        ])
    
    html_parts.append('</div>')
    
    return "\n".join(html_parts)


def _format_size(bytes_value: int) -> str:
    """Format bytes to human-readable size"""
    if bytes_value is None or bytes_value == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"


def _format_duration(seconds: float) -> str:
    """Format seconds to human-readable duration"""
    if seconds < 60:
        return f"{seconds:.1f} сек"
    elif seconds < 3600:
        return f"{seconds/60:.1f} мин"
    else:
        return f"{seconds/3600:.1f} ч"
