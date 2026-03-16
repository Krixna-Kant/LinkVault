# LinkVault

> Save links. Never miss a deadline.

LinkVault is a smart link reminder tool. Paste a URL — a job posting, hackathon, event, or anything with a deadline — and the AI will classify it, extract the deadline, and surface it before the opportunity expires.

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your OPENAI_API_KEY to .env

python run.py
# API running at http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# UI running at http://localhost:3000
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React (Vite)  →  /api proxy  →  Flask  →  SQLite           │
│                                    ↓                         │
│                              AI Service (OpenAI)             │
│                              Scraper (BeautifulSoup)         │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | What it must NOT do |
|---|---|---|
| `models/` | SQLAlchemy schema + helper methods | Business logic, DB queries |
| `schemas/` | Pydantic validation, AI output contract | DB access |
| `services/` | Business logic, AI calls, DB writes | Flask request objects |
| `routes/` | HTTP routing, parsing, response codes | SQL queries, business rules |
| React `hooks/` | Server state management | Direct fetch calls |
| React `components/` | Rendering, local UI state | API calls |

---

## Key Technical Decisions

### 1. AI Classifier with Guaranteed Fallback

The AI service (`app/services/ai_service.py`) uses a strict system prompt that forces the model to return only valid JSON matching the `LinkAnalysis` schema. If the model returns garbage, a network error occurs, or it hallucinates — the fallback path kicks in silently:

```python
# The save operation NEVER fails because of AI
except (OpenAIError, json.JSONDecodeError, ValueError) as e:
    logger.warning("AI analysis failed, using fallback. Reason: %s", e)
    return _fallback(scraped_title)
```

This was a deliberate choice: a reminder tool that fails to save because of an AI error would be untrustworthy. The AI is an enhancement, not a hard dependency.

### 2. Pydantic Schemas as the API Contract

All inputs are validated via Pydantic before touching the service layer. This means:
- Invalid URLs are rejected at the route level (422), not the DB level
- Deadlines in the past are rejected at write time
- `reminder_at` must be before `deadline` — enforced by a `model_validator`

This prevents invalid state from ever entering the system.

### 3. Enum-Based State Machine

A link's `status` is strictly `pending | done | expired`. No string literals. This prevents accidental invalid states:

```python
class LinkStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    EXPIRED = "expired"
```

`sync_expired_links()` runs on app startup to auto-transition past-deadline links.

### 4. Scraper Never Crashes the Save

The scraper (`scraper_service.py`) catches all exceptions and returns a `ScrapedPage(ok=False)` on failure. The AI service then runs on partial data. The link is always saved.

### 5. App Factory Pattern

`create_app()` accepts a config dict, making the app fully testable with an in-memory SQLite DB without any test-specific code paths.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/links/` | Save and analyze a new link |
| `GET` | `/api/links/` | List all links (filter by `status`, `category`) |
| `GET` | `/api/links/:id` | Get a single link |
| `PATCH` | `/api/links/:id` | Update status, notes, deadline |
| `DELETE` | `/api/links/:id` | Delete a link |
| `POST` | `/api/links/sync-expired` | Mark past-deadline links as expired |

### Save a Link

```bash
curl -X POST http://localhost:5000/api/links/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://devfolio.co/some-hackathon", "notes": "Team already formed"}'
```

Response:
```json
{
  "id": 1,
  "url": "https://devfolio.co/some-hackathon",
  "title": "HackIndia 2024 — Build with AI",
  "summary": "A national hackathon focused on AI applications. Register before Aug 31.",
  "category": "hackathon",
  "priority": "high",
  "deadline": "2024-08-31T23:59:00+00:00",
  "reminder_at": "2024-08-30T23:59:00+00:00",
  "status": "pending",
  "expiring_soon": false,
  "notes": "Team already formed",
  "created_at": "2024-08-10T10:00:00+00:00"
}
```

---

## AI Guidance

See `claude.md` for the full constraints file used to guide AI agents working on this codebase.

Key constraints:
- AI classifier must return only valid JSON from a fixed category enum
- `deadline` must be `null` if not clearly present — never hallucinate dates
- All AI failures must fall back silently, never crashing the save
- No new routes without a Pydantic schema

---

## Tradeoffs and Weaknesses

### Known Weaknesses

**No auth** — This is a single-user, local-first tool. Adding auth would require a User model, JWT middleware, and per-user DB isolation. Described as a future extension in the walkthrough.

**No real-time reminders** — Reminders are surfaced as UI badges ("Expiring Soon"), not push notifications or emails. Adding a notification layer (APScheduler + SMTP or Resend) is the clearest extension path.

**Scraping reliability** — Some sites (LinkedIn, Instagram) block scrapers. The fallback ensures the link saves, but AI analysis quality degrades. A browser extension that passes pre-rendered HTML would fix this cleanly.

**AI deadline extraction accuracy** — GPT-4o-mini is fast and cheap but less precise than GPT-4o for date extraction from ambiguous text. Upgrading the model or adding a date-parsing post-processing step would improve accuracy.

### Extension Approach

1. **Browser Extension** — Right-click → "Save to LinkVault" passes the URL and pre-rendered HTML directly, bypassing scraping limits
2. **Email/Push reminders** — APScheduler polls `links` table for `reminder_at < now` and fires via Resend or Pushover
3. **Multi-user** — Add `User` model, Flask-JWT-Extended, and a `user_id` FK on `Link`
4. **Re-analysis** — "Refresh" button re-scrapes and re-analyzes a saved link to catch updated deadlines

---

## Project Structure

```
linkvault/                 
├── backend/
│   ├── run.py
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── __init__.py          # App factory
│       ├── extensions.py        # SQLAlchemy instance
│       ├── models/
│       │   └── link.py          # Link ORM model + enums
│       ├── schemas/
│       │   └── link_schema.py   # Pydantic validation schemas
│       ├── services/
│       │   ├── ai_service.py    # OpenAI classifier + fallback
│       │   ├── scraper_service.py
│       │   └── link_service.py  # Core business logic
│       └── routes/
│           └── links.py         # Flask routes
│   └── tests/
│       ├── conftest.py
│       ├── test_ai_service.py
│       ├── test_link_service.py
│       └── test_routes.py
└── frontend/
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── index.css
        ├── services/api.js      # Axios API layer
        ├── hooks/useLinks.js    # Server state hook
        └── components/
            ├── AddLinkForm.jsx
            ├── LinkCard.jsx
            └── FilterBar.jsx
```
