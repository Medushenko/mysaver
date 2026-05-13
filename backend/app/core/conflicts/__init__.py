"""
Conflicts package initialization
"""
from app.core.conflicts.resolver import ConflictPolicy, ConflictResolver, FileInfo, ResolutionResult
from app.core.conflicts.report import ConflictReport, ConflictEntry

__all__ = [
    'ConflictPolicy',
    'ConflictResolver',
    'FileInfo',
    'ResolutionResult',
    'ConflictReport',
    'ConflictEntry',
]
