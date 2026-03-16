# LinkVault — AI Guidance File

This file constrains how AI agents (Claude, Copilot, etc.) should behave when working on this codebase.

---

## Project Purpose

LinkVault is a smart link reminder tool. Users paste URLs; the system scrapes the page, uses an LLM to classify the link type and extract any deadline, then surfaces reminders before opportunities expire.

---

## Architecture Overview

```
React (Vite) → Flask REST API → SQLite (via SQLAlchemy) → AI Service (OpenAI)
```

Layers must remain strictly separated:
- `models/` — SQLAlchemy ORM only. No business logic.
- `schemas/` — Pydantic validation only. No DB access.
- `services/` — Business logic and AI calls. No Flask request objects.
- `routes/` — Flask routing only. Delegates to services. No SQL queries.

---

## AI Service Constraints

### The AI classifier MUST:
- Return ONLY valid JSON matching `LinkAnalysis` schema (see `services/ai_service.py`)
- Use the exact category enum: `["job", "hackathon", "event", "article", "product", "course", "other"]`
- Return `null` for `deadline` if no deadline is detectable — never hallucinate a date
- Return `priority` as one of: `["high", "medium", "low"]` only

### The AI classifier MUST NOT:
- Return free-form text outside the JSON envelope
- Invent deadlines that are not present or strongly implied in the page content
- Access external URLs itself — it receives scraped text only

### Fallback behavior (REQUIRED):
If the AI call fails or returns unparseable output, the system MUST fall back to:
```python
LinkAnalysis(
    category="other",
    title=<og:title or URL hostname>,
    summary="Could not analyze link.",
    deadline=None,
    priority="medium"
)
```
Never let an AI failure crash the save operation.

---

## Validation Rules (never relax these)

- URLs must be HTTP/HTTPS and parseable by `urllib.parse`
- `deadline` if provided must be a future date (validated at write time)
- `status` is an enum: `pending | done | expired` — no other values allowed
- `reminder_at` must be before `deadline` if both are set

---

## What AI Agents Should NOT Do

- Do not add authentication/auth middleware — out of scope
- Do not change the DB schema without updating both the model and the migration
- Do not inline SQL — use SQLAlchemy ORM only
- Do not add new API routes without a corresponding Pydantic schema
- Do not catch bare `Exception` — catch specific exceptions and log them
- Do not remove the AI fallback path

---

## Test Expectations

Every service function must have at least one test covering:
1. The happy path
2. Invalid input rejection
3. AI failure fallback (for `ai_service.py`)

---

## Code Style

- Python: PEP8, type hints on all function signatures, docstrings on all service functions
- React: functional components only, no class components
- No `any` types in TypeScript-style prop definitions
- Keep components under 150 lines — split if larger
