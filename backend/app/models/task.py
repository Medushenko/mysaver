"""
Task model
"""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, BigInteger, Text, DateTime, ForeignKey, Index, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class TaskStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ConflictPolicy(str, PyEnum):
    SKIP = "skip"
    OVERWRITE = "overwrite"
    KEEP_BOTH = "keep_both"
    RENAME = "rename"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    source_provider: Mapped[str] = mapped_column(String(64))
    source_path: Mapped[str] = mapped_column(String(1024))
    dest_provider: Mapped[str] = mapped_column(String(64))
    dest_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[TaskStatus] = mapped_column(
        String(16),
        default=TaskStatus.PENDING
    )
    bytes_planned: Mapped[int] = mapped_column(BigInteger, default=0)
    bytes_done: Mapped[int] = mapped_column(BigInteger, default=0)
    error_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    options: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # New fields for parsed links and conflict policy
    parsed_links: Mapped[list] = mapped_column(JSON, default=list)
    conflict_policy: Mapped[Optional[ConflictPolicy]] = mapped_column(
        SQLEnum(ConflictPolicy),
        nullable=True
    )
    preview_tree: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_user_id_status", "user_id", "status"),
    )

    def to_dict(self) -> dict:
        """Return brief status dict for API"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "source": f"{self.source_provider}:{self.source_path}",
            "destination": f"{self.dest_provider}:{self.dest_path}",
            "bytes_planned": self.bytes_planned,
            "bytes_done": self.bytes_done,
            "error_reason": self.error_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parsed_links": self.parsed_links,
            "conflict_policy": self.conflict_policy.value if self.conflict_policy else None,
            "preview_tree": self.preview_tree,
        }
