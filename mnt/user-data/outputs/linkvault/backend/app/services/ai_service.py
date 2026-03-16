"""
AI Service — calls OpenAI to classify a link and extract structured metadata.

Constraints (see claude.md):
- Returns LinkAnalysis with safe defaults on ANY failure
- Never invents deadlines not present in scraped content
- Only returns categories from LinkCategory enum
"""

import json
import logging
from typing import Optional

from openai import OpenAI, OpenAIError

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
  "deadline": "ISO 8601 datetime string if a clear deadline/closing date exists, otherwise null",
  "priority": one of ["high", "medium", "low"] based on time-sensitivity
}

Rules:
- Set deadline to null if no deadline is clearly stated or strongly implied
- Never hallucinate dates
- Set priority "high" only if deadline is within 7 days or opportunity seems urgent
- Return nothing outside the JSON object — no explanation, no markdown
"""


def _fallback(title: str) -> LinkAnalysis:
    """Safe fallback when AI analysis fails."""
    return LinkAnalysis(
        category=LinkCategory.OTHER,
        title=title[:100] if title else "Untitled",
        summary="Could not analyze link.",
        deadline=None,
        priority=LinkPriority.MEDIUM,
    )


def analyze_link(scraped_title: str, scraped_text: str, client: Optional[OpenAI] = None) -> LinkAnalysis:
    """
    Analyze scraped page content using OpenAI and return structured LinkAnalysis.
    Falls back to safe defaults on any failure.

    Args:
        scraped_title: Page title from scraper
        scraped_text: Body text (truncated) from scraper
        client: Optional OpenAI client (injectable for testing)

    Returns:
        LinkAnalysis — always valid, never raises
    """
    if client is None:
        try:
            client = OpenAI()
        except Exception as e:
            logger.warning("Could not initialize OpenAI client: %s", e)
            return _fallback(scraped_title)

    user_content = f"Title: {scraped_title}\n\nContent:\n{scraped_text[:3000]}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=400,
        )

        raw = response.choices[0].message.content or ""
        data = json.loads(raw.strip())
        return LinkAnalysis(**data)

    except (OpenAIError, json.JSONDecodeError, ValueError) as e:
        logger.warning("AI analysis failed, using fallback. Reason: %s", e)
        return _fallback(scraped_title)
    except Exception as e:
        logger.error("Unexpected error in AI analysis: %s", e)
        return _fallback(scraped_title)
