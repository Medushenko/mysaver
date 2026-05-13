"""
Schemas for preview API endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PreviewNode(BaseModel):
    """Schema for a node in the preview tree"""
    id: str
    name: str
    type: str  # file|folder
    size: int = 0
    children: List['PreviewNode'] = Field(default_factory=list)
    checked: bool = True
    path: str = ""
    
    class Config:
        from_attributes = True


# Update forward reference
PreviewNode.model_rebuild()


class StatsSchema(BaseModel):
    """Schema for tree statistics"""
    total_files: int = 0
    total_folders: int = 0
    total_size: int = 0


class PreviewResponse(BaseModel):
    """Response schema for preview endpoint"""
    task_id: str
    tree: PreviewNode
    stats: StatsSchema
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "tree": {
                    "id": "root-1",
                    "name": "Documents",
                    "type": "folder",
                    "size": 0,
                    "children": [
                        {
                            "id": "file-1",
                            "name": "report.pdf",
                            "type": "file",
                            "size": 1024000,
                            "children": [],
                            "checked": True,
                            "path": "/Documents/report.pdf"
                        }
                    ],
                    "checked": True,
                    "path": "/Documents"
                },
                "stats": {
                    "total_files": 1,
                    "total_folders": 1,
                    "total_size": 1024000
                }
            }
        }


class ConflictPolicyRequest(BaseModel):
    """Request schema for conflict resolution"""
    task_id: str
    policy: str = Field(..., description="Conflict policy: skip, overwrite, keep_both, rename")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy": "skip"
            }
        }


class ConflictReportSchema(BaseModel):
    """Schema for conflict report"""
    task_id: str
    policy: str
    total_conflicts: int
    summary: Dict[str, int]
    conflicts: List[Dict[str, Any]]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ConflictResponse(BaseModel):
    """Response schema for conflicts endpoint"""
    report: ConflictReportSchema
    
    class Config:
        json_schema_extra = {
            "example": {
                "report": {
                    "task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "policy": "skip",
                    "total_conflicts": 1,
                    "summary": {"skipped": 1, "overwritten": 0, "renamed": 0},
                    "conflicts": [],
                    "started_at": "2024-01-01T00:00:00",
                    "completed_at": "2024-01-01T00:00:01"
                }
            }
        }
