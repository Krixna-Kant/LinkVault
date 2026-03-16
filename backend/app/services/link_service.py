"""
Link Service — core business logic for saving, listing, and updating links.

Rules:
- No Flask request objects here
- No raw SQL — SQLAlchemy ORM only
- AI failure must never prevent saving a link
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.extensions import db
from app.models.link import Link, LinkStatus
from app.schemas.link_schema import SaveLinkRequest, UpdateLinkRequest
from app.services.scraper_service import scrape_url
from app.services.ai_service import analyze_link

logger = logging.getLogger(__name__)


def save_link(req: SaveLinkRequest) -> Link:
    """
    Scrape the URL, analyze with AI, persist and return the Link.

    The save succeeds even if scraping or AI analysis fails.
    """
    url_str = str(req.url)

    # Step 1: Scrape
    page = scrape_url(url_str)

    # Step 2: AI analysis (always returns valid LinkAnalysis)
    analysis = analyze_link(page.title, page.text)

    # Step 3: Persist
    link = Link(
        url=url_str,
        title=analysis.title,
        summary=analysis.summary,
        category=analysis.category,
        priority=analysis.priority,
        deadline=analysis.deadline,
        notes=req.notes,
        status=LinkStatus.PENDING,
    )

    # Auto-set reminder to 24h before deadline if deadline exists
    if analysis.deadline:
        from datetime import timedelta
        link.reminder_at = analysis.deadline - timedelta(hours=24)

    db.session.add(link)
    db.session.commit()

    logger.info("Saved link id=%d category=%s url=%s", link.id, link.category, url_str[:60])
    return link


def list_links(
    status: Optional[str] = None,
    category: Optional[str] = None,
) -> list[Link]:
    """Return all links, optionally filtered by status and/or category."""
    query = Link.query

    if status:
        try:
            query = query.filter(Link.status == LinkStatus(status))
        except ValueError:
            pass  # Invalid status filter → ignore, return all

    if category:
        from app.models.link import LinkCategory
        try:
            query = query.filter(Link.category == LinkCategory(category))
        except ValueError:
            pass

    return query.order_by(Link.created_at.desc()).all()


def get_link(link_id: int) -> Optional[Link]:
    """Return a single link by ID, or None."""
    return db.session.get(Link, link_id)


def update_link(link_id: int, req: UpdateLinkRequest) -> Optional[Link]:
    """
    Partially update a link. Only provided fields are changed.
    Returns None if link not found.
    """
    link = db.session.get(Link, link_id)
    if link is None:
        return None

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(link, field, value)

    link.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return link


def delete_link(link_id: int) -> bool:
    """Delete a link. Returns True if deleted, False if not found."""
    link = db.session.get(Link, link_id)
    if link is None:
        return False
    db.session.delete(link)
    db.session.commit()
    return True


def sync_expired_links() -> int:
    """
    Mark all past-deadline pending links as expired.
    Call this on app startup or via a scheduled job.
    Returns count of links updated.
    """
    now = datetime.now(timezone.utc)
    expired = (
        Link.query
        .filter(Link.status == LinkStatus.PENDING)
        .filter(Link.deadline.isnot(None))
        .filter(Link.deadline < now)
        .all()
    )
    for link in expired:
        link.status = LinkStatus.EXPIRED
        link.updated_at = now

    if expired:
        db.session.commit()
        logger.info("Marked %d links as expired", len(expired))

    return len(expired)
