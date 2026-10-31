# Empório da Música — agent instructions

> Read this first, every session. It holds what is not in the code. The roadmap is in `docs/SESSIONS.md` and the current state in `docs/PROGRESS.md`.

## What this is

A text customer-service agent for Empório da Música, a fictional instrument store in Campo Grande/MS, built for the Artefact AI Engineer challenge. Breno owns the decisions.

The project uses:
- Python, FastAPI and Gemini with function calling;
- SQLite;
- policy retrieval by manual section;
- an HTML interface with the Ressonância brand;
- a Cloud Run demo.

State on 2026-10-31 20:18 São Paulo: S0–S8 done. Revision `emporio-agent-00011-z2g` (commit `ec6f6d6`) is the delivered version; README, reviewed examples, security (D23) and the delivery PDF are done. C10 waits only for Breno to upload the PDF and reply to the e-mail. Details and the deploy command are in the `docs/PROGRESS.md` resume block.

## Tie-breaking requirement

> A wrong price, order access or deadline fails the case, even with a friendly tone. When a fact is missing, the agent asks the customer or prepares a hand-off. It never makes things up.

## Inviolable rules

- **Deadline and delivery:**
  - freeze on **Tue 2026-11-03 23:59 São Paulo time** (D11);
  - delivery is a PDF in English named `Breno Zamponi - AI Engineer – Full-Stack para Aplicações com IA Generativa`, uploaded to the Google Form, plus a reply to the e-mail with the repository link (D17). Breno submits.
- **Language (D16):**
  - repository, code, comments, docs, commit messages and the PDF are in **English**;
  - the agent's replies to customers and the UI text are in **Brazilian Portuguese**.
- **Secrets and private inputs never enter Git:**
  - `.env`;
  - Gemini, GCP and GitHub keys;
  - `_private_inputs/` (ZIPs, PDFs, raw CSVs, internal guides);
  - derived databases;
  - customer name, e-mail and phone.

  Before each commit: `git add`, then `.venv/bin/python scripts/check_staged.py` must print PASS.
- **Money in integer cents.** Values come from `Decimal` built from the CSV string, with `ROUND_HALF_UP` once. The LLM never computes prices; it receives values confirmed by the backend.
- **Identity comes from the server session.** An order number typed in chat identifies the record, not the customer. Another profile's order gets the same answer as a non-existent one.
- **Real execution is the evidence.** Mocks are for tests and are labeled as mocks. `examples/` holds real captures of the delivered version. Prepared examples from the guides do not count.
- **Actions without an integration are never claimed as done.** A hand-off stays `prepared`; no "we registered it", no ticket numbers.
- **Fix first.** Do not build on a known defect without Breno's authorization. Deploys, billable resources and sending e-mail need authorization at the time.

## Source of truth

| Question | Source (local: `_private_inputs/`) |
| --- | --- |
| Deliverables and deadline | Artefact case PDF (`challenge/`) and the selection e-mail (D11, D17) |
| Store rules | Manual v2.1 (`challenge/.../data/políticas_da_loja.pdf`); a decisive gap or conflict leads to a hand-off |
| Product, price, stock, order | The 6 CSVs (`challenge/.../data/`) |
| Brand and screen | Guide 01 (`guides/01-branding/`) and the mockup in `visual-references/`, with a single avatar per turn |
| Technical contracts | Guide 02 (`guides/02-backend/`); expected values in `tests/fixtures/oracles.json`; contract examples in `tests/fixtures/turns.json` (not versioned) |
| Applying references and skills | Guide 03 (`guides/03-vision/`) |

## Boundaries in force

| Boundary | Rule |
| --- | --- |
| Agent SQL | Only `catalog.db`, read-only, deny-by-default authorizer. Orders use a separate connection |
| Installments | Where §3 and §3.1 diverge, return `needs_confirmation` and offer an option valid under every reading |
| Third-party skills | Installed in `.claude/skills/` and ignored by Git (see `docs/references-and-skills.md`) |
| GCP | **Only the `emporio-da-musica-agent` project. Never use `altivaserra`, which belongs to another of Breno's projects and remains the active `default` gcloud configuration.** Every gcloud command for this repo runs with `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio` and `--project emporio-da-musica-agent`, region `southamerica-east1`. Do not change the active global configuration. |

## Where things are

| | |
| --- | --- |
| `docs/SESSIONS.md` | Roadmap and "▶️ Start the next session here" |
| `docs/PROGRESS.md` | Current state and "resume here" |
| `docs/DECISIONS.md` | Decisions, each with the trigger that reopens it |
| `docs/source-findings.md` | Discrepancies between data, manual and guides |
| `docs/architecture.md` | Components and planned tree |
| `docs/JOURNAL.md` · `docs/ERRORS.md` | One entry per session · error catalog by class |
| `docs/ai-usage.md` | Real log of Claude Code and ChatGPT usage (deliverable) |

## Commands

```bash
.venv/bin/python -m pytest                    # gates (snapshot tests need _private_inputs/ or EMPORIO_SNAPSHOT)
.venv/bin/python scripts/mutation_check.py    # every mutation must be caught
.venv/bin/python scripts/import_snapshot.py   # rebuild data/build/ from _private_inputs/challenge
.venv/bin/python scripts/check_staged.py      # before every commit
```

## Protocol

- **Opening a session:** read this file, then `docs/PROGRESS.md`, then `git status`.
- **Closing:** gates read, two review passes, documents updated, commit with the why.
- **On finding a defect:** open `docs/ERRORS.md` before fixing it.
