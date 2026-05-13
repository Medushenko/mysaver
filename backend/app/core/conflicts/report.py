"""
Conflict report generation
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.conflicts.resolver import ResolutionResult, ConflictPolicy


@dataclass
class ConflictEntry:
    """Single conflict entry in the report"""
    source_path: str
    destination_path: str
    resolution: ResolutionResult
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "resolution": self.resolution.to_dict(),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ConflictReport:
    """Report of all conflicts encountered during an operation"""
    task_id: str
    policy: ConflictPolicy
    conflicts: List[ConflictEntry] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    @property
    def total_conflicts(self) -> int:
        """Total number of conflicts"""
        return len(self.conflicts)
    
    @property
    def summary(self) -> Dict[str, int]:
        """Summary of actions taken"""
        summary = {
            'skipped': 0,
            'overwritten': 0,
            'renamed': 0,
            'copied': 0
        }
        
        for conflict in self.conflicts:
            action = conflict.resolution.action_taken
            if action in summary:
                summary[action] += 1
        
        return summary
    
    def add_conflict(
        self,
        source_path: str,
        destination_path: str,
        resolution: ResolutionResult
    ):
        """Add a conflict entry to the report"""
        entry = ConflictEntry(
            source_path=source_path,
            destination_path=destination_path,
            resolution=resolution
        )
        self.conflicts.append(entry)
    
    def complete(self):
        """Mark the report as completed"""
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "policy": self.policy.value,
            "total_conflicts": self.total_conflicts,
            "summary": self.summary,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConflictReport':
        """Create ConflictReport from dictionary"""
        report = cls(
            task_id=data.get('task_id', ''),
            policy=ConflictPolicy(data.get('policy', 'skip')),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else datetime.now()
        )
        
        for conflict_data in data.get('conflicts', []):
            resolution = ResolutionResult(
                action_taken=conflict_data.get('resolution', {}).get('action_taken', 'skipped'),
                new_path=conflict_data.get('resolution', {}).get('new_path'),
                checksum_match=conflict_data.get('resolution', {}).get('checksum_match', False),
                warning=conflict_data.get('resolution', {}).get('warning')
            )
            
            entry = ConflictEntry(
                source_path=conflict_data.get('source_path', ''),
                destination_path=conflict_data.get('destination_path', ''),
                resolution=resolution,
                timestamp=datetime.fromisoformat(conflict_data.get('timestamp', datetime.now().isoformat()))
            )
            report.conflicts.append(entry)
        
        if data.get('completed_at'):
            report.completed_at = datetime.fromisoformat(data['completed_at'])
        
        return report
