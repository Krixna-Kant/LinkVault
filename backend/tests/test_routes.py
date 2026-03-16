"""
Integration tests for Flask routes.
Tests the full request → response cycle with mocked services.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.models.link import LinkStatus, LinkCategory, LinkPriority
from app.schemas.link_schema import LinkAnalysis


MOCK_ANALYSIS = LinkAnalysis(
    category=LinkCategory.JOB,
    title="Engineer at Acme",
    summary="Great role.",
    deadline=None,
    priority=LinkPriority.MEDIUM,
)


@patch("app.services.link_service.analyze_link", return_value=MOCK_ANALYSIS)
@patch("app.services.link_service.scrape_url")
class TestSaveLinkRoute:
    def test_post_valid_url_returns_201(self, mock_scrape, mock_ai, client):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="Test", text="", ok=True)

        res = client.post("/api/links/", json={"url": "https://example.com"})
        assert res.status_code == 201
        data = res.get_json()
        assert data["title"] == "Engineer at Acme"
        assert data["status"] == "pending"

    def test_post_invalid_url_returns_422(self, mock_scrape, mock_ai, client):
        res = client.post("/api/links/", json={"url": "not-a-url"})
        assert res.status_code == 422

    def test_post_missing_url_returns_422(self, mock_scrape, mock_ai, client):
        res = client.post("/api/links/", json={})
        assert res.status_code == 422


class TestGetLinksRoute:
    @patch("app.services.link_service.analyze_link", return_value=MOCK_ANALYSIS)
    @patch("app.services.link_service.scrape_url")
    def test_get_returns_list(self, mock_scrape, mock_ai, client):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="Test", text="", ok=True)
        client.post("/api/links/", json={"url": "https://example.com"})

        res = client.get("/api/links/")
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)
        assert len(res.get_json()) >= 1

    def test_get_nonexistent_id_returns_404(self, client):
        res = client.get("/api/links/99999")
        assert res.status_code == 404


class TestUpdateLinkRoute:
    @patch("app.services.link_service.analyze_link", return_value=MOCK_ANALYSIS)
    @patch("app.services.link_service.scrape_url")
    def test_patch_status(self, mock_scrape, mock_ai, client):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="Test", text="", ok=True)

        res = client.post("/api/links/", json={"url": "https://example.com"})
        link_id = res.get_json()["id"]

        patch_res = client.patch(f"/api/links/{link_id}", json={"status": "done"})
        assert patch_res.status_code == 200
        assert patch_res.get_json()["status"] == "done"

    def test_patch_nonexistent_returns_404(self, client):
        res = client.patch("/api/links/99999", json={"status": "done"})
        assert res.status_code == 404


class TestDeleteLinkRoute:
    @patch("app.services.link_service.analyze_link", return_value=MOCK_ANALYSIS)
    @patch("app.services.link_service.scrape_url")
    def test_delete_existing(self, mock_scrape, mock_ai, client):
        from app.services.scraper_service import ScrapedPage
        mock_scrape.return_value = ScrapedPage(title="Test", text="", ok=True)

        res = client.post("/api/links/", json={"url": "https://example.com"})
        link_id = res.get_json()["id"]

        del_res = client.delete(f"/api/links/{link_id}")
        assert del_res.status_code == 200
        assert del_res.get_json()["deleted"] is True

    def test_delete_nonexistent_returns_404(self, client):
        res = client.delete("/api/links/99999")
        assert res.status_code == 404
