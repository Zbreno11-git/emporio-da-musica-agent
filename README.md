# Empório da Música · customer-service agent

A Python prototype of a text-based customer-service agent for **Empório da Música**, a fictional musical-instrument store in Campo Grande/MS, Brazil. The project is my answer to the Artefact AI Engineer technical challenge.

The agent answers questions about the catalog, prices, payment methods, orders and store policies. It queries the data when it needs a fact and the store manual when it needs a rule. When information is missing, it asks the customer or prepares a hand-off to the staff.

> **Language.** The repository, code and documentation are in English, as required by the selection process. The agent talks to customers in **Brazilian Portuguese**, because the store and its customers are in Brazil and the challenge asks for a persona aligned with the store. The example conversations are kept in Portuguese with an English translation alongside ([D16](docs/DECISIONS.md)).

## Status (2026-10-31)

**Work in progress.** Milestone 1 works with real Gemini: the Takamine GD20 price (R$ 2.199,00) and the follow-up "e no PIX?" (R$ 2.089,05) in the same session ([evidence](evals/milestone1-smoke.md)).

| Done | Next |
| --- | --- |
| Snapshot importer (CSV → SQLite) with validation and a manifest | Cloud Run deploy |
| Price, PIX and installment rules in integer cents, tested against reference values | Model cost-benefit benchmark |
| Read-only catalog SQL executor with a deny-by-default authorizer | Ressonância web UI |
| Gemini function-calling loop with per-turn budget and server-side checks of prices and claimed actions | Browser tests, real captured conversations |
| FastAPI session, dedup, rate limit and public errors | |
| Orders bound to the session's demo profile; section-level manual retrieval ([evaluation](evals/policy-retrieval.md)); prepared hand-offs | |

The roadmap is in [`docs/SESSIONS.md`](docs/SESSIONS.md) and the current state in [`docs/PROGRESS.md`](docs/PROGRESS.md).

## Stack

| Piece | Choice | Details |
| --- | --- | --- |
| Language and API | Python 3.12, FastAPI, Pydantic v2 | [architecture](docs/architecture.md) |
| Model | Gemini with function calling (`google-genai` SDK) | The exact model is chosen by a cost-benefit benchmark ([D14](docs/DECISIONS.md)) |
| Data | Read-only SQLite for the catalog, a separate database for orders | Money in integer cents, computed deterministically |
| Policies | Retrieval by manual section | Lexical first; semantic only if the evaluation shows a gain |
| Interface | HTML, CSS and JS served by FastAPI, "Ressonância" visual identity | |
| Demo | A single GCP Cloud Run service | The same app runs locally |

All decisions and their reopening triggers are in [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Local setup

The challenge data (CSVs and store manual) is **not** versioned ([D15](docs/DECISIONS.md)). You need the ZIP provided by Artefact.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env            # set GEMINI_API_KEY locally; never commit .env

# Build the demo databases and the manual index from the challenge ZIP (or the extracted directory)
.venv/bin/python scripts/import_snapshot.py --source "path/to/Desafio_Técnico_AI_Engineer_2026-....zip"
.venv/bin/python scripts/build_policy_index.py --source "path/to/Desafio_Técnico_AI_Engineer_2026-....zip"

# Tests (no API key needed). Snapshot-based tests read EMPORIO_SNAPSHOT=<ZIP> or skip with a reason.
EMPORIO_SNAPSHOT="path/to/the/zip" .venv/bin/python -m pytest
.venv/bin/python scripts/mutation_check.py     # curated mutations that the tests must catch
```

Run the app locally (needs `GEMINI_API_KEY` and `GEMINI_MODEL` in `.env`):

```bash
.venv/bin/uvicorn app.main:get_app --factory --port 8000    # then open http://localhost:8000
.venv/bin/python scripts/smoke_gemini.py --model gemini-3.1-flash-lite   # milestone-1 check with the real API
```

## Repository layout

The planned code layout is in [`docs/architecture.md`](docs/architecture.md#planned-tree).

```text
app/main.py               FastAPI routes, session cookie, public errors
app/agent.py              Gemini tool loop, per-turn budget, response composition and text checks
app/prompts.py            store persona (instructions in English, replies in Brazilian Portuguese)
app/session.py            in-memory sessions, dedup, rate limit
app/tools/quote.py        price, promotion, PIX and installments (cents)
app/tools/catalog.py      restricted SQL executor + product hydration
app/tools/orders.py       order lookup bound to the session's demo profile
app/tools/policies.py     BM25 retrieval over manual sections + related-section expansion
scripts/build_policy_index.py  manual PDF -> section index (pages, tables, related ids)
scripts/eval_retrieval.py labeled retrieval evaluation
app/contracts.py          HTTP request/response models
scripts/smoke_gemini.py   milestone-1 check against the real API
evals/                    smoke and benchmark evidence
scripts/import_snapshot.py  CSV -> SQLite with validation and manifest
scripts/check_staged.py   pre-commit scan for secrets, personal data and manual excerpts
scripts/mutation_check.py curated mutation net
tests/                    domain and tool tests
docs/                     architecture, decisions, findings, roadmap, progress, AI usage
```

## Use of AI assistants

See [`docs/ai-usage.md`](docs/ai-usage.md). It is updated throughout the project and separates what each tool did from the decisions I made and how I verified the results.
