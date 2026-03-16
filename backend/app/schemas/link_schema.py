"""
Pydantic schemas — validate all API inputs and structure AI outputs.
These are the contract between the outside world and our services.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator, model_validator
from app.models.link import LinkCategory, LinkPriority, LinkStatus


# ── Request Schemas ────────────────────────────────────────────────────────────

class SaveLinkRequest(BaseModel):
    url: HttpUrl
    notes: Optional[str] = None

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v: HttpUrl) -> HttpUrl:
        if str(v).startswith("javascript:") or str(v).startswith("data:"):
            raise ValueError("URL scheme not allowed")
        return v


class UpdateLinkRequest(BaseModel):
    status: Optional[LinkStatus] = None
    notes: Optional[str] = None
    deadline: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    priority: Optional[LinkPriority] = None

    @model_validator(mode="after")
    def reminder_before_deadline(self) -> "UpdateLinkRequest":
        if self.reminder_at and self.deadline:
            if self.reminder_at >= self.deadline:
                raise ValueError("reminder_at must be before deadline")
        return self

    @field_validator("deadline", mode="before")
    @classmethod
    def deadline_must_be_future(cls, v):
        if v is None:
            return v
        dt = v if isinstance(v, datetime) else datetime.fromisoformat(str(v))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt <= datetime.now(timezone.utc):
            raise ValueError("deadline must be in the future")
        return dt


# ── AI Service Schema ──────────────────────────────────────────────────────────

class LinkAnalysis(BaseModel):
    """
    Structured output from the AI classifier.
    All fields have safe defaults — AI failure must never crash the save.
    """
    category: LinkCategory = LinkCategory.OTHER
    title: str = "Untitled"
    summary: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: LinkPriority = LinkPriority.MEDIUM

    @field_validator("category", mode="before")
    @classmethod
    def coerce_category(cls, v):
        try:
            return LinkCategory(v)
        except ValueError:
            return LinkCategory.OTHER

    @field_validator("priority", mode="before")
    @classmethod
    def coerce_priority(cls, v):
        try:
            return LinkPriority(v)
        except ValueError:
            return LinkPriority.MEDIUM
