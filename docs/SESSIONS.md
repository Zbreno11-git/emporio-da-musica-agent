# Roadmap

Each session is a 1–2 hour package that ends with something verifiable and gets a journal entry. Checkpoint status lives in [`PROGRESS.md`](PROGRESS.md).

**Progress: 6 of 11 sessions closed** (S0, S0b, S1, S-EN, S2, S3). S4–S8 are next.

Each session is tagged by the kind of check it needs:
- **[OFF]** runs offline;
- **[GEM]** needs real Gemini;
- **[URL]** must pass on the hosted URL.

> **Order notes.**
> - 2026-10-31: Breno approved the two-day plan; execution started that same evening, ahead of day 1.
> - 2026-10-31: the selection e-mail moved the deadline to **Tue 2026-11-03 23:59 São Paulo time** (D11) and required English (D16) and a PDF via Google Forms (D17).
>   - Session S-EN was inserted before S2 to translate the repository.
>   - S8 moved to 2026-11-03 and now includes the delivery PDF.
>   - Nov 2 stays as the internal "code complete" target.

## ▶️ Start the next session here

See the "RESUME HERE" block in [`PROGRESS.md`](PROGRESS.md).

## Breno's answers (2026-10-31)

| Question | Answer | Consequence |
| --- | --- | --- |
| Deadline | Freeze Tue 2026-11-03 23:59 São Paulo time | Code complete by 2026-11-02; Nov 3 for capture, PDF and review |
| Benchmark models | `gemini-3.1-flash-lite` × `gemini-3.5-flash` | Two rows in S5; smoke test with both in S2 |
| Budget | US$ 5 total | BRL billing: budget equivalent to US$ 5, filtered to `emporio-da-musica-agent` and `gen-lang-client-0041725501`, alerts at 50/90/100%. **The budget alerts, it does not cap**, hence the limits in code |
| Gemini key | Keep the current one everywhere | Goes to the Empório project's Secret Manager on deploy; other uses of the key count against the cap |
| Delivery blockers | Cross-profile leak · divergent price or promotion · claimed action not executed | Each becomes an automated test and a verdict item; latency is only measured |
| Language | English repository; Portuguese customer-facing agent | All new code and docs in English; examples in PT with EN translation |
| Delivery | PDF via Google Forms + e-mail reply | S8 produces the PDF; Breno submits |

## Checkpoint map

| C | Closes when | Type | Depends on |
| --- | --- | --- | --- |
| C0 | Answers and plan recorded (commit `docs: plano de dois dias`) | OFF | — |
| C1 | `pytest tests/domain` green: import + quote match 100% of `oracles.json` | OFF | C0 |
| C2 | SQL executor blocks every violation class | OFF | C1 |
| C-EN | Repository in English; tests and mutations still green | OFF | C2 |
| C3 | Milestone 1: Takamine GD20 R$ 2.199,00 → "e no PIX?" R$ 2.089,05 via `/api/chat` | GEM | C-EN |
| C4 | Orders bound to the session: A sees order 8, cross-profile = non-existent | OFF + GEM | C3 |
| C5 | Policy retrieval: ≥10/12 in top 3, plus mixed questions recorded | OFF | C1 |
| C6 | First Cloud Run revision answers milestone 1 in an incognito window | URL | C3, C4 |
| C7 | Benchmark picks and pins `GEMINI_MODEL` | GEM | C4, C5 |
| C8 | Ressonância UI checked at 320, 390 px and desktop | OFF + GEM | C3 |
| C9 | Playwright + failure tests green, new revision live | OFF + URL | C6, C8 |
| C10 | 5 real conversations on the URL, reviewed, no blocker; final README; clean clone reproduces; delivery PDF ready | URL | C7, C9 |

---

## ✅ S0 · Setup and first push (2026-10-31)
- [x] Inputs in the ignored private folder; `.venv` with Python 3.12.3
- [x] Oracles × CSVs: 0 differences; findings recorded
- [x] Three project skills installed; dedicated GCP project created (no billing yet)
- [x] Public repository, commit `00e9e7f` verified

## ✅ S0b · Plan recorded (2026-10-31)
- [x] Decisions D11–D15, roadmap, pre-commit scan in `scripts/check_staged.py` — commit `fde18b1`

## ✅ S1 · Data and deterministic rules (2026-10-31) [OFF]
- [x] 1.1 Dependencies pinned (`requirements.txt` frozen from a clean venv; `pip check` clean)
- [x] 1.2 Importer: counts 9/65/25/50/20/22, `sellable=61`, `dataset_id 1412d32a6eeb` from both ZIP and directory; 6 invalid-row classes abort with line and reason — commit `6b08e6e`
- [x] 1.3 Quote: 9 products and 3 orders match the oracles; R$ 600 in 12x rejected — commit `99baaa2`
- [x] 1.4 SQL executor: violations blocked, nylon up to R$ 800 → 83, 85, 81, 84 — commit `6059b51`
- [x] Mutation net: 15/15 caught (`scripts/mutation_check.py`)

## ✅ S-EN · Translate the repository to English (2026-10-31) [OFF]
- [x] Code, comments, messages, tests, docs and file names in English; private folder renamed to `_private_inputs/`
- **✅ C-EN:** `pytest` green, 15/15 mutations, `check_staged.py` PASS, no Portuguese outside customer-facing strings and data.

## Day 1 · 2026-11-01

### ✅ S2 · First turn with real Gemini (done 2026-10-31, ahead of schedule) [GEM]
- [x] Agent loop, session, API, minimal page; 76 tests, 23/23 mutations; milestone 1 passes with both candidates ([evidence](../evals/milestone1-smoke.md))
- **2.1** `app/contracts.py` (done in draft); the contract examples validate.
- **2.2 Agent loop.**
  - **Does:** `app/agent.py` with `generate_content`, manual dispatch, model content parts preserved (thought signatures), a budget of 3 rounds, 6 tools and 25 s, and cards hydrated by the backend; the system prompt and customer replies are in PT-BR.
  - **🐞** Signature lost between rounds → log the raw parts.
- **2.3 Minimal API.**
  - **Does:** `app/session.py` (RAM, cookie, TTL, dedup); `app/main.py` (`/api/session`, `/api/chat`, `/healthz`); minimal page.
- **2.4 Smoke.**
  - **Does:** `scripts/smoke_gemini.py --model X` with both candidates.
  - **✅ C3:** 219900 then 208905, same `product_id=95`, via `quote_product(method=pix)`; log model, SDK version, duration and tokens.
- **Offline tests:** HTTP with a labeled fake Gemini (contract, 409, 410, 503).

### ✅ S3 · Orders and policies (done 2026-10-31, ahead of schedule) [OFF + GEM]
- [x] Orders bound to the session with profile rotation; manual index (28 sections) and BM25 with related sections (12/12 base); prepared hand-off with the §7 channel; 95 tests, 29/29 mutations; real scenarios checked and two prompt fixes applied
- **3.1 Orders.**
  - **Does:** `app/tools/orders.py` with `WHERE order_id=? AND customer_id=?`; profiles demo-a→2, demo-b→6, demo-c→7; a profile switch clears history and cache.
  - **✅ C4:** A/8 `shipped`; B/9 `confirmed`; B/8 == B/999; visitor → `profile_required`.
- **3.2 Manual.** `scripts/build_policy_index.py` → `data/build/policy_sections.json`; manual review of §3/3.1, §4, §5, §6.2 and §8.
- **3.3 Retrieval.**
  - **Does:** BM25 in `app/tools/policies.py`; `evals/policy_retrieval.jsonl` (12 base cases, 6 paraphrases, 4 mixed).
  - **✅ C5:** top 3 ≥ 10/12.
- **3.4 [GEM]** Order 8 with profile A; shipping of exactly R$ 500 → `contact_store` + hand-off `prepared`.

### S4 · First deploy (≈1.5 h) [URL]
- **Mandatory pause:** Breno confirms the billing link and budget at the time, because they cost money.
- **4.1 Accounts.**
  - **Does:** with `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio`:
    - link billing;
    - create a BRL budget with `--filter-projects` on the 2 projects;
    - enable run, cloudbuild, artifactregistry and secretmanager;
    - create the secret from the key via stdin, readable only by the service account.
- **4.2 Deploy.**
  - **Does:** `Dockerfile` (python:3.12-slim); `.gcloudignore` audited with `gcloud meta list-files-for-upload`; `gcloud run deploy --source . --region southamerica-east1 --max-instances 1 --min-instances 0`.
  - **✅ C6:** `/healthz` 200; milestone 1 via curl on the URL; incognito window; revision and commit noted in the README.

## Day 2 · 2026-11-02 (code complete)

### S5 · Cost-benefit benchmark (≈1.5 h) [GEM]
- **Does:** `scripts/benchmark_models.py`, 2 models × 2 repetitions over the fixed battery:
  - Takamine → PIX;
  - Kalani on PIX;
  - nylon up to R$ 800;
  - order 8 as A and as B;
  - return with a missing fact;
  - out of scope;
  - shipping of exactly R$ 500.

  Measures the 3 blockers against oracles and profile, tool and arguments, cold and warm latency, and tokens (`usage_metadata`). Cost only with a price verified that day.
- **Selection rule (D14):** the cheapest model that passes the 3 blockers in every run; tie → lower median latency.
- **✅ C7:** `evals/model-benchmark.md`; `GEMINI_MODEL` pinned; spend checked in billing.

### S6 · Ressonância interface (≈2 h) [OFF + GEM]
- **Does:** `/frontend-design` with guide 01. The screen has:
  - exact tokens and local WOFF2 fonts (OFL);
  - slogan and 3 suggestions at the opening, collapsed on first send;
  - speech before cards and **one avatar per turn**;
  - card with name, attribute, price (list, % and current) and availability in words;
  - profile selector only on `choose_profile`;
  - copyable hand-off summary;
  - sources on demand, `aria-live`, collapsed technical panel;
  - "Tentar novamente" that keeps the draft.

  UI text is in PT-BR.
- **✅ C8:** screenshots at 320, 390 and 1280 px; name and price legible; card price == DTO.

### S7 · Browser, failures and second revision (≈1.5 h) [OFF + URL]
- **Does:** `/webapp-testing` with Playwright in Python and 2 isolated contexts:
  - Takamine → PIX;
  - order 8 as a visitor, with the wrong profile and with a profile switch;
  - provider error via the labeled fake;
  - no `networkidle`, no sleeps.

  Failures: 504, 429, empty tool result, resend with the same `request_id`, concurrent 409, and 410.
- **✅ C9:** `pytest` and `pytest tests/e2e` green; the new revision answers milestone 1.

## Day 3 · 2026-11-03 (freeze 23:59 São Paulo)

### S8 · Real capture, review and delivery (≈2–3 h, done by 20:00) [URL]
- **8.1 Capture.** 5 conversations on the URL (discovery, promotion + PIX, authorized order, return, out of scope) in `examples/*.md`. Each is in PT-BR with an English translation, model, commit, manifest, tools, duration and a screenshot.
- **8.2 Review.** `/qa-response` on each, with tool results and manual sections. A blocker means fix the cause and capture again.
- **8.3 Final README.** Setup, decisions, limitations, AI usage, URL and revision; reproduction from a clean clone.
- **8.4 Delivery PDF.** English, named `Breno Zamponi - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf`, with repository link, demo URL, decision summary and examples index. A reply text for the e-mail is also prepared.
- **✅ C10:** 5/5 without blockers; `scripts/check_staged.py` PASS; `git ls-remote` == HEAD; last commit before 23:59 São Paulo on 2026-11-03; PDF handed to Breno.

## Risks

- **Billing, budget and deploy cost money:** confirmation at the time.
- **The budget only alerts:** limits in code (length, rounds, 10 turns/min per session, max 1 instance) do the containment.
- **The same key is used outside the project:** check spend at the end of S2, S5 and S8.
- **Gemini 3.x function calling:** preserve content parts; flash-lite may pick the wrong tool, which the benchmark measures.
- **In-memory session:** an instance recycle loses the session. Mitigation: max 1 instance, 410 tested.
- **Cut order if late:** technical panel → semantic search → animations → second benchmark repetition. **Never cut:** blockers, real capture, reproducible README, the PDF.

## Definition of done (delivery)

- C0–C10 closed, each with the literal command line quoted in `PROGRESS.md`.
- URL serving the delivered commit.
- 3–5 real conversations without blockers.
- README reproduced from a clean clone.
- AI usage recorded.
- PDF uploaded by Breno.
- Nothing changed after 2026-11-03 23:59 São Paulo.
