"""
Tests for AI service — especially fallback behavior.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from app.services.ai_service import analyze_link
from app.models.link import LinkCategory, LinkPriority


class TestAnalyzeLink:
    def test_happy_path_returns_valid_analysis(self):
        """AI returns valid JSON → parse into LinkAnalysis correctly."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=json.dumps({
                            "category": "job",
                            "title": "Senior Engineer at Acme",
                            "summary": "A great job posting for engineers.",
                            "deadline": "2099-12-31T23:59:00",
                            "priority": "high",
                        })
                    )
                )
            ]
        )

        result = analyze_link("Senior Engineer at Acme", "Apply by Dec 31", client=mock_client)

        assert result.category == LinkCategory.JOB
        assert result.title == "Senior Engineer at Acme"
        assert result.priority == LinkPriority.HIGH
        assert result.deadline is not None

    def test_fallback_on_json_decode_error(self):
        """If AI returns garbage, fallback gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="not json at all!!!"))]
        )

        result = analyze_link("Some Title", "Some content", client=mock_client)

        assert result.category == LinkCategory.OTHER
        assert result.summary == "Could not analyze link."
        assert result.deadline is None

    def test_fallback_on_openai_error(self):
        """If OpenAI raises, fallback gracefully."""
        from openai import OpenAIError
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = OpenAIError("rate limited")

        result = analyze_link("Title", "Content", client=mock_client)

        assert result.category == LinkCategory.OTHER
        assert result.priority == LinkPriority.MEDIUM

    def test_invalid_category_coerced_to_other(self):
        """AI returns unknown category → coerced to 'other'."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=json.dumps({
                            "category": "unicorn_category",
                            "title": "Test",
                            "summary": "Test",
                            "deadline": None,
                            "priority": "medium",
                        })
                    )
                )
            ]
        )

        result = analyze_link("Test", "Test", client=mock_client)
        assert result.category == LinkCategory.OTHER
