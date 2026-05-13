"""
Preview API endpoints - GET /api/v1/preview/{task_id}, POST /api/v1/conflicts
"""
import uuid
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.schemas.preview import (
    PreviewResponse,
    PreviewNode,
    StatsSchema,
    ConflictPolicyRequest,
    ConflictResponse,
    ConflictReportSchema
)
from app.core.preview import TreeBuilder, PreviewTree
from app.core.conflicts import ConflictResolver, ConflictPolicy, FileInfo, ConflictReport
from app.models.task import Task
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()

# In-memory storage for preview trees (in production, use Redis/database)
_preview_trees: Dict[str, PreviewTree] = {}
_conflict_reports: Dict[str, ConflictReport] = {}


@router.get("/preview/{task_id}", response_model=PreviewResponse)
async def get_preview(task_id: str):
    """
    Get preview tree for a task
    
    Returns the file hierarchy tree with statistics for the given task ID.
    The tree shows files and folders that will be copied/synced.
    """
    # Check if we have a cached tree for this task
    if task_id in _preview_trees:
        tree = _preview_trees[task_id]
        stats = tree.get_stats()
        
        return PreviewResponse(
            task_id=task_id,
            tree=PreviewNode(**tree.to_dict()),
            stats=StatsSchema(**stats)
        )
    
    # Try to get from database
    async with get_db() as db:
        result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # If task has preview_tree stored
        if task.preview_tree:
            tree_dict = task.preview_tree
            return PreviewResponse(
                task_id=task_id,
                tree=PreviewNode(**tree_dict),
                stats=StatsSchema(
                    total_files=len([n for n in str(tree_dict).split('"type": "file"')]) - 1,
                    total_folders=len([n for n in str(tree_dict).split('"type": "folder"')]) - 1,
                    total_size=0
                )
            )
    
    raise HTTPException(status_code=404, detail=f"No preview available for task {task_id}")


@router.post("/preview/build", response_model=PreviewResponse)
async def build_preview(task_id: str, link_url: str, provider: str, link_type: str):
    """
    Build preview tree from a link
    
    Creates a preview tree by fetching file listing from the source.
    """
    from app.core.parsers.base import LinkInfo
    
    link = LinkInfo(
        url=link_url,
        provider=provider,
        type=link_type,
        metadata={}
    )
    
    builder = TreeBuilder()
    tree = await builder.build_tree(link)
    
    # Cache the tree
    _preview_trees[task_id] = tree
    
    # Update database if task exists
    async with get_db() as db:
        result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
        task = result.scalar_one_or_none()
        
        if task:
            task.preview_tree = tree.to_dict()
            await db.commit()
    
    stats = tree.get_stats()
    
    return PreviewResponse(
        task_id=task_id,
        tree=PreviewNode(**tree.to_dict()),
        stats=StatsSchema(**stats)
    )


@router.post("/conflicts", response_model=ConflictResponse)
async def resolve_conflicts(request: ConflictPolicyRequest):
    """
    Resolve conflicts for a task using specified policy
    
    Applies the conflict resolution policy to all conflicting files
    and returns a report of actions taken.
    """
    policy = ConflictPolicy(request.policy)
    
    # Create a mock conflict report for demonstration
    # In real implementation, this would analyze actual file conflicts
    report = ConflictReport(
        task_id=request.task_id,
        policy=policy
    )
    
    # Get task info to find potential conflicts
    async with get_db() as db:
        result = await db.execute(select(Task).where(Task.id == uuid.UUID(request.task_id)))
        task = result.scalar_one_or_none()
        
        if task:
            # Update task with conflict policy
            task.conflict_policy = policy
            await db.commit()
            
            # Simulate conflict resolution based on parsed links
            for link_info in task.parsed_links:
                # This is simplified - real implementation would check actual destination
                src_file = FileInfo(
                    path=link_info.get('url', ''),
                    name=link_info.get('url', '').split('/')[-1],
                    size=0
                )
                dst_file = FileInfo(
                    path=f"/destination/{src_file.name}",
                    name=src_file.name,
                    size=0
                )
                
                result = ConflictResolver.resolve(src_file, dst_file, policy)
                report.add_conflict(
                    source_path=src_file.path,
                    destination_path=dst_file.path,
                    resolution=result
                )
    
    report.complete()
    
    # Store report
    _conflict_reports[request.task_id] = report
    
    return ConflictResponse(
        report=ConflictReportSchema(
            task_id=report.task_id,
            policy=report.policy.value,
            total_conflicts=report.total_conflicts,
            summary=report.summary,
            conflicts=[c.to_dict() for c in report.conflicts],
            started_at=report.started_at.isoformat(),
            completed_at=report.completed_at.isoformat() if report.completed_at else None
        )
    )


@router.get("/conflicts/{task_id}", response_model=ConflictResponse)
async def get_conflicts(task_id: str):
    """
    Get conflict report for a task
    """
    if task_id in _conflict_reports:
        report = _conflict_reports[task_id]
        return ConflictResponse(
            report=ConflictReportSchema(
                task_id=report.task_id,
                policy=report.policy.value,
                total_conflicts=report.total_conflicts,
                summary=report.summary,
                conflicts=[c.to_dict() for c in report.conflicts],
                started_at=report.started_at.isoformat(),
                completed_at=report.completed_at.isoformat() if report.completed_at else None
            )
        )
    
    raise HTTPException(status_code=404, detail=f"No conflict report for task {task_id}")
