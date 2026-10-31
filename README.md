# Empório da Música · customer-service agent

A Python prototype of a text-based customer-service agent for **Empório da Música**, a fictional musical-instrument store in Campo Grande/MS, Brazil. The project is my answer to the Artefact AI Engineer technical challenge.

The agent answers questions about the catalog, prices, payment methods, orders and store policies. It queries the data when it needs a fact and the store manual when it needs a rule. When information is missing, it asks the customer or prepares a hand-off to the staff.

> **Language.** The repository, code and documentation are in English, as required by the selection process. The agent talks to customers in **Brazilian Portuguese**, because the store and its customers are in Brazil and the challenge asks for a persona aligned with the store. The example conversations are kept in Portuguese with an English translation alongside ([D16](docs/DECISIONS.md)).

## Status (2026-10-31)

**Work in progress.** Data import, deterministic pricing and the restricted catalog SQL executor are done and tested. The LLM agent loop is next.

| Done | Next |
| --- | --- |
| Snapshot importer (CSV → SQLite) with validation and a manifest | Gemini function-calling loop: Takamine GD20 price (R$ 2.199,00) → "e no PIX?" (R$ 2.089,05) |
| Price, PIX and installment rules in integer cents, tested against reference values | Orders bound to the server session, policy retrieval by manual section |
| Read-only catalog SQL executor with a deny-by-default authorizer | Ressonância web UI, Cloud Run deploy, real captured conversations |

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

# Build the demo databases from the challenge ZIP (or a directory containing the 6 CSVs)
.venv/bin/python scripts/import_snapshot.py --source "path/to/Desafio_Técnico_AI_Engineer_2026-....zip"

# Tests (no API key needed). Snapshot-based tests read EMPORIO_SNAPSHOT=<ZIP> or skip with a reason.
EMPORIO_SNAPSHOT="path/to/the/zip" .venv/bin/python -m pytest
.venv/bin/python scripts/mutation_check.py     # curated mutations that the tests must catch
```

The commands to run the web app are added together with the first chat endpoint.

## Repository layout

The planned code layout is in [`docs/architecture.md`](docs/architecture.md#planned-tree).

```text
app/tools/quote.py        price, promotion, PIX and installments (cents)
app/tools/catalog.py      restricted SQL executor + product hydration
app/contracts.py          HTTP request/response models
scripts/import_snapshot.py  CSV -> SQLite with validation and manifest
scripts/check_staged.py   pre-commit scan for secrets, personal data and manual excerpts
scripts/mutation_check.py curated mutation net
tests/                    domain and tool tests
docs/                     architecture, decisions, findings, roadmap, progress, AI usage
```

## Use of AI assistants

See [`docs/ai-usage.md`](docs/ai-usage.md). It is updated throughout the project and separates what each tool did from the decisions I made and how I verified the results.
