"""
Link model — single source of truth for DB schema.
Business logic lives in services/, not here.
"""

import enum
from datetime import datetime, timezone

from app.extensions import db


class LinkStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    EXPIRED = "expired"


class LinkCategory(str, enum.Enum):
    JOB = "job"
    HACKATHON = "hackathon"
    EVENT = "event"
    ARTICLE = "article"
    PRODUCT = "product"
    COURSE = "course"
    OTHER = "other"


class LinkPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Link(db.Model):
    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)

    # AI-analyzed fields
    title = db.Column(db.String(512), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    category = db.Column(db.Enum(LinkCategory), nullable=False, default=LinkCategory.OTHER)
    priority = db.Column(db.Enum(LinkPriority), nullable=False, default=LinkPriority.MEDIUM)

    # Deadline & reminder
    deadline = db.Column(db.DateTime(timezone=True), nullable=True)
    reminder_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # State
    status = db.Column(db.Enum(LinkStatus), nullable=False, default=LinkStatus.PENDING)
    notes = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def _aware_deadline(self):
        """Return deadline as timezone-aware datetime, regardless of how it was stored."""
        if self.deadline is None:
            return None
        if self.deadline.tzinfo is None:
            return self.deadline.replace(tzinfo=timezone.utc)
        return self.deadline

    def is_expiring_soon(self, within_hours: int = 48) -> bool:
        """Return True if deadline is within `within_hours` and link is still pending."""
        if self.status != LinkStatus.PENDING or self.deadline is None:
            return False
        now = datetime.now(timezone.utc)
        delta = self._aware_deadline() - now
        return 0 < delta.total_seconds() <= within_hours * 3600

    def is_expired(self) -> bool:
        """Return True if deadline has passed and link is still pending."""
        if self.deadline is None:
            return False
        return datetime.now(timezone.utc) > self._aware_deadline()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "summary": self.summary,
            "category": self.category.value,
            "priority": self.priority.value,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "reminder_at": self.reminder_at.isoformat() if self.reminder_at else None,
            "status": self.status.value,
            "notes": self.notes,
            "expiring_soon": self.is_expiring_soon(),
            "is_expired": self.is_expired(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }