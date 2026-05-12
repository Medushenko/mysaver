"""
SQLAlchemy Base and Mixins
"""
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    @declared_attr
    def created_at(cls):
        return DateTime(timezone=True), {"default": lambda: datetime.now(timezone.utc)}
    
    @declared_attr
    def updated_at(cls):
        return DateTime(
            timezone=True,
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc)
        )


class Base(DeclarativeBase):
    """Base class for all models"""
    pass
