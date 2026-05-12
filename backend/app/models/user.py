"""
User model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_id: Mapped[str] = mapped_column(String(32), default='free')
    monthly_bytes_quota: Mapped[int] = mapped_column(
        BigInteger,
        default=10737418240  # 10 GB
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now
    )

    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Return dict representation without sensitive data"""
        return {
            "id": str(self.id),
            "email": self.email,
            "is_pro": self.is_pro,
            "plan_id": self.plan_id,
            "monthly_bytes_quota": self.monthly_bytes_quota,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
