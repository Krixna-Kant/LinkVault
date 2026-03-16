"""
AI Service — calls Google Gemini (free tier) to classify links.
Falls back to safe defaults on any failure.
"""

import json
import logging
import os
from typing import Optional

from google import genai
from google.genai.errors import APIError

from app.schemas.link_schema import LinkAnalysis
from app.models.link import LinkCategory, LinkPriority

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a link classifier for a reminder tool.
Given the title and text content of a webpage, extract structured information.

You MUST respond with ONLY valid JSON matching this exact schema:
{
  "category": one of ["job", "hackathon", "event", "article", "product", "course", "other"],
  "title": "concise title of the page (max 100 chars)",
  "summary": "1-2 sentence summary of what this is",
  "deadline": "ISO 8601 datetime string if a clear deadline exists, otherwise null",
  "priority": one of ["high", "medium", "low"] based on time-sensitivity
}

Rules:
- Set deadline to null if no deadline is clearly stated
- Never hallucinate dates
- Return ONLY the JSON object, no explanation, no markdown
"""


def _fallback(title: str) -> LinkAnalysis:
    return LinkAnalysis(
        category=LinkCategory.OTHER,
        title=title[:100] if title else "Untitled",
        summary="Could not analyze link.",
        deadline=None,
        priority=LinkPriority.MEDIUM,
    )


def analyze_link(scraped_title: str, scraped_text: str, client=None) -> LinkAnalysis:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set, using fallback")
        return _fallback(scraped_title)

    try:
        # The new SDK automatically picks up GEMINI_API_KEY from the environment
        client_instance = client or genai.Client()
        
        user_content = f"Title: {scraped_title}\n\nContent:\n{scraped_text[:3000]}\n\nSystem Instruction: {SYSTEM_PROMPT}"
        
        response = client_instance.models.generate_content(
            model="gemini-3-flash-preview",
            contents=user_content,
        )

        raw = response.text.strip()
        # Strip markdown code fences if Gemini adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw.strip())
        return LinkAnalysis(**data)

    except (APIError, json.JSONDecodeError, ValueError) as e:
        logger.warning("Gemini analysis failed, using fallback. Reason: %s", e)
        return _fallback(scraped_title)
    except Exception as e:
        logger.error("Unexpected error in AI analysis: %s", e)
        return _fallback(scraped_title)