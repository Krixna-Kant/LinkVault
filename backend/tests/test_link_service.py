"""
Tests for link_service — happy paths, validation, edge cases.
"""

import pytest
from unittest.mock import patch
from app.services import link_service
from app.schemas.link_schema import SaveLinkRequest, UpdateLinkRequest
from app.models.link import LinkStatus, LinkCategory, LinkPriority
from app.schemas.link_schema import LinkAnalysis


MOCK_ANALYSIS = LinkAnalysis(
    category=LinkCategory.JOB,
    title="Software Engineer at Acme",
    summary="Great job opportunity.",
    deadline=None,
    priority=LinkPriority.HIGH,
)


@patch("app.services.link_service.analyze_link", return_value=MOCK_ANALYSIS)
@patch("app.services.link_service.scrape_url")
class TestSaveLink:
    def test_happy_path_saves_link(self, mock_scrape, mock_ai, app):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="Acme Job", text="Apply here", ok=True)

        req = SaveLinkRequest(url="https://example.com/job")
        link = link_service.save_link(req)

        assert link.id is not None
        assert link.title == "Software Engineer at Acme"
        assert link.category == LinkCategory.JOB
        assert link.status == LinkStatus.PENDING

    def test_saves_with_notes(self, mock_scrape, mock_ai, app):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="Test", text="", ok=True)

        req = SaveLinkRequest(url="https://example.com", notes="Apply before Friday")
        link = link_service.save_link(req)

        assert link.notes == "Apply before Friday"

    def test_scrape_failure_still_saves(self, mock_scrape, mock_ai, app):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="example.com", text="", ok=False)

        req = SaveLinkRequest(url="https://example.com/broken")
        link = link_service.save_link(req)

        assert link.id is not None
        assert link.status == LinkStatus.PENDING


class TestUpdateLink:
    @patch("app.services.link_service.analyze_link", return_value=MOCK_ANALYSIS)
    @patch("app.services.link_service.scrape_url")
    def test_mark_done(self, mock_scrape, mock_ai, app):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="Test", text="", ok=True)

        req = SaveLinkRequest(url="https://example.com")
        link = link_service.save_link(req)

        updated = link_service.update_link(link.id, UpdateLinkRequest(status=LinkStatus.DONE))
        assert updated.status == LinkStatus.DONE

    def test_update_nonexistent_link_returns_none(self, app):
        result = link_service.update_link(99999, UpdateLinkRequest(status=LinkStatus.DONE))
        assert result is None


class TestDeleteLink:
    @patch("app.services.link_service.analyze_link", return_value=MOCK_ANALYSIS)
    @patch("app.services.link_service.scrape_url")
    def test_delete_existing(self, mock_scrape, mock_ai, app):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="Test", text="", ok=True)

        req = SaveLinkRequest(url="https://example.com")
        link = link_service.save_link(req)

        assert link_service.delete_link(link.id) is True
        assert link_service.get_link(link.id) is None

    def test_delete_nonexistent_returns_false(self, app):
        assert link_service.delete_link(99999) is False


class TestSyncExpired:
    @patch("app.services.link_service.analyze_link")
    @patch("app.services.link_service.scrape_url")
    def test_marks_past_deadline_as_expired(self, mock_scrape, mock_ai, app):
        from datetime import datetime, timezone, timedelta
        from app.services.scraper_service import ScrapedPage

        past_deadline = LinkAnalysis(
            category=LinkCategory.HACKATHON,
            title="Past Hackathon",
            summary="Already over.",
            deadline=datetime(2000, 1, 1, tzinfo=timezone.utc),
            priority=LinkPriority.HIGH,
        )
        mock_ai.return_value = past_deadline
        mock_scrape.return_value = ScrapedPage(title="Hackathon", text="", ok=True)

        req = SaveLinkRequest(url="https://example.com/hackathon")
        link = link_service.save_link(req)

        # Manually force deadline to past since schema rejects past dates on update
        from app.extensions import db
        link.deadline = datetime(2000, 1, 1, tzinfo=timezone.utc)
        link.status = LinkStatus.PENDING
        db.session.commit()

        count = link_service.sync_expired_links()
        assert count >= 1

        refreshed = link_service.get_link(link.id)
        assert refreshed.status == LinkStatus.EXPIRED
