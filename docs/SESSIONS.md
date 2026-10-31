# Roadmap

Each session is a 1–2 hour package that ends with something verifiable and gets a journal entry. Checkpoint status lives in [`PROGRESS.md`](PROGRESS.md).

**Progress: 8 of 13 sessions closed** (S0, S0b, S1, S-EN, S2, S3, S4, S5 benchmark). Next: S5.2 cost model, S5.3, S6, S6b, S7, S8.

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
| C7b | Cost model `evals/cost-model.md` (D19) | OFF | C7 |
| C8b | `/admin` with token, aggregates only (D20) | OFF + GEM | C8 |
| C9 | Playwright + failure tests green, QA report with screenshots (D21), new revision live | OFF + URL | C6, C8, C8b |
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

### ✅ S4 · First deploy (done 2026-10-31) [URL]
- [x] Billing via D18, budget R$ 30, secret scoped to the service account, revision `emporio-agent-00002-8wx` from `37c5597`; `/health` 200, milestone 1 on the URL, 410 without a session. `/healthz` is reserved by Cloud Run (ERRORS class 3)
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

### ✅ S5 · Cost-benefit benchmark (done 2026-10-31) [GEM]
- [x] 3 models × 2 runs × 9 turns; 0 blocker turns for all; `gemini-3.1-flash-lite` pinned by D14 ([report](../evals/model-benchmark.md))

> **Plan for the remaining sessions** (written 2026-10-31 16:40 SP after the compact; facts measured that day: Playwright browsers cached but the Python package not installed, node v24 present, no pandoc; `evals/pricing.json` not shipped in the image; the out-of-scope run 2 named "Ibanez GSR200" with no tool result — a product claim without evidence, treated as a defect in S5.3).

### Schedule (São Paulo time)
| When | Sessions | Checkpoint |
| --- | --- | --- |
| Sat 31/10, evening | S5.2 cost model, S5.3 prompt fix | C7b |
| Sun 01/11 | S6 UI, S6b `/admin` | C8, C8b |
| Mon 02/11 | S7 testing & hardening, second revision. **Code complete** | C9 |
| Tue 03/11, done by 20:00 | S8 capture, review, README, clean clone, PDF | C10 |

If the work runs late, cut in this order (unchanged):
1. technical panel;
2. animations;
3. the 1280 px screenshot set;
4. the BRL conversion in the cost model.

**Never cut:** the blockers, the real capture, the reproducible README, the PDF.

---

### S5.2 · Cost model (≈1 h) [OFF + one web fetch] → C7b
**Does:** add `scripts/cost_model.py`.
- **Inputs:**
  - `evals/benchmark/2026-10-31-{gemini-3.1-flash-lite,gemini-3.5-flash-lite}.jsonl`;
  - `evals/pricing.json`.

  It reuses `cost_usd` from `scripts/benchmark_models.py` by import, so the formula has one source (thinking tokens are billed as output).
- **Output:** `evals/cost-model.md` (plus `--json` for the PDF), with these sections.
  1. **Per answer:** the mean, median and max cost per turn, and the mean number of model calls per turn, for each model.
  2. **Per turn type:** quote, catalog search, order, policy, hand-off and out of scope. Columns: turns, average input, average output plus thinking, and average cost.
  3. **Monthly projection:** 500, 2,000 and 10,000 conversations, at a stated assumption of **4 turns per conversation**. Each row multiplies the measured mean cost per turn, so the arithmetic is visible.
  4. **Sensitivity:**
     - 2 turns and 8 turns per conversation;
     - an "every turn costs like the most expensive type" line;
     - a history-growth line from the measured Takamine step 0 → 1 input delta (5457 → 6010 tokens).
  5. **Model lines:**
     - `3.5-flash-lite` is the migration path after the 2027-05-07 shutdown;
     - the price doubling of `3.6-flash` on 2027-01-01 is noted only.
  6. **Cloud Run as a separate line.** Fetch the official Cloud Run pricing page that day and record the URL and the date in a new `"cloud_run"` block in `pricing.json`. Use the `southamerica-east1` tier and request-based billing with min-instances 0.
     - Estimate vCPU-seconds and GiB-seconds from the measured median turn latency (1.85 s × turns) at 1 vCPU / 0.5 GiB, and requests at about 2 per turn (chat + static).
     - Show it with and without the monthly free tier. Concurrency of 20 makes this an upper bound; say so.
  7. **BRL:** state one USD→BRL rate with its source (the Banco Central PTAX of the last business day) and its date. The client is a Brazilian store.
  8. **Caveats:**
     - 18 turns per model;
     - the benchmark's turn-type mix is not the store's real mix;
     - token counts include the about 6k tokens of tool schema and system prompt per call.

**✅ C7b:**
- `.venv/bin/python scripts/cost_model.py` prints the `3.1-flash-lite` mean of **0.00167 USD/turn**, which must match `benchmark_models.py --summarize-only`, and the `3.5-flash-lite` mean of **0.00224**.
- The projection rows equal mean × 4 × volume. For example, 2,000 conversations → about **US$ 13.4/month** of Gemini on `3.1-flash-lite`.
- A test (`tests/evals/test_cost_model.py`) recomputes one row from 2 synthetic usage rows by hand.
- A mutation in `mutation_check.py` (thinking tokens dropped from the output cost) must be caught by it.

**🐞 Expected trouble:**
- The Cloud Run page may show a different tier or table layout → record exactly what was read, with the date, and mark the number "estimate".

### S5.3 · Out-of-scope fix (≈30 min) [GEM]
**Does:**
1. **Prompt (`app/prompts.py`):**
   - rule 1 gains "never name a product, model or brand the store sells unless it came from a tool result in this conversation";
   - the "What the store sells" paragraph gains: "for the instrument part of a mixed question, call query_catalog before suggesting anything".
2. **Benchmark (`benchmark_models.py`):** the `out_of_scope` step gets a new blocker check: any capitalized model name in the text must belong to a card. This is implemented as "the text names no product from the catalog that is not on a card", with names checked against `catalog.db`. Two invented names still need a non-catalog check, so a second **quality** check flags "a bass was recommended but no cards".
3. **Re-run:** add `--scenarios` to the benchmark and rerun `out_of_scope` ×2 plus `takamine_pix` ×1 (regression) on `3.1-flash-lite`.

**✅ Checkpoint:**
- 2/2 out-of-scope runs call `query_catalog`, return at least one available bass card, and name no product that is not on a card;
- Takamine is still 219900 → 208905;
- the result is appended to `evals/model-benchmark.md` with its date.

**🐞 Expected trouble:**
- If lite still skips the tool → a server-side text check in `check_text`: a catalog product name in the text without a card counts as unsupported, with one correction and then the fallback.
- That check becomes a new mutation.

### S6 · Ressonância UI (≈2.5 h) [OFF + GEM] → C8
**Read first:** `/frontend-design`, `frontend-e-ux`, the full guide 01 (§4 tokens, §5 conversation anatomy, §7 acceptance list), and the mockup `_private_inputs/guides/01-branding/assets/ui-opcao-1-emporio_mockup.png`.

**Does:** split `app/static/` into `index.html` + `app.css` + `app.js`, with no inline script so that S7's CSP can forbid it.
- **Brand:**
  - exact tokens from guide 01 §4;
  - Fraunces 600 and Source Sans 3 (400/600/700) as local WOFF2 (latin + latin-ext), from `@fontsource` on jsdelivr, with `OFL.txt` alongside and `font-display: swap`;
  - one avatar per agent turn.
- **Opening:** the slogan and 3 suggestion chips, collapsed after the first send.
- **Cards** (built in `app.js` from the DTO only):
  - name, attribute, availability in words;
  - the price block shows the list price struck through, the percentage and the current price when `discount_percent > 0`, otherwise the current price;
  - `payment_cents` with its method when present.
- **Formatting:** BRL with `Intl.NumberFormat('pt-BR')` from cents, through one pure `formatCents()` function.
- **Interaction:**
  - the profile selector (from `/api/demo-profiles`) appears only on `next_action=choose_profile`;
  - the hand-off box shows the summary, the channel and a "Copiar resumo" button, and the text "Resumo preparado";
  - sources sit behind a "Fontes" toggle;
  - `aria-live="polite"` on the log;
  - a typing indicator;
  - on an error, the message and "Tentar novamente" re-send the same `request_id` and keep the draft;
  - a 410 starts a new session and says so;
  - a technical panel, collapsed, shows `trace` when present.
- **Language:** all UI text is PT-BR.

**✅ C8:**
- Run locally with real Gemini: the Takamine → PIX flow.
- Playwright screenshots at 320, 390 and 1280 px go to `docs/qa/screens/` (the S7 numbering starts here).
- Visual review of each screenshot against the mockup and the guide §7 checklist.
- In the DOM, the card's price text equals `formatCents(dto.offer_cents)`, i.e. "R$ 2.199,00", then "R$ 2.089,05".
- The 320 px page has no horizontal scroll (`scrollWidth <= innerWidth`).

**🐞 Expected trouble:**
- A non-breaking space in the `Intl` output breaks string asserts → normalize ` ` in the tests only.
- Fonts not loading → check the network panel and the `/static` MIME type.

### S6b · `/admin` (≈1.5 h) [OFF + GEM] → C8b — D20
**Does:**
- **`app/metrics.py`:** a `TurnMetrics` collector, in memory and thread-safe, with `started_at`. It is fed in `main.py` after each successful turn, with `record(trace, cards, sources)`. It stores **only**:
  - the cost (usage × the price for `settings.gemini_model`);
  - a topic label;
  - the product ids and names from cards.

  It never stores the message, the text or the hand-off summary. Topic derivation is a pure function `topic_for(tools, sources, handoff)`:
  - `get_my_order` → "Pedido";
  - `prepare_handoff` → "Atendimento humano (<reason>)";
  - `search_policy` with section X → "Política §X <title>";
  - `quote_product` with pix → "Preço / PIX";
  - other `quote_product` → "Preço / pagamento";
  - `query_catalog` → "Busca no catálogo";
  - no tool → "Sem consulta (conversa/fora de escopo)".
- **Pricing:** shipped. `Dockerfile` adds `COPY evals/pricing.json`, `.gcloudignore` allows it, and `Settings.pricing_path` points to it. It stays one file; the model's price comes from it, and a missing price shows "custo indisponível", never 0.
- **Routes:**
  - `GET /admin` serves a static shell (`noindex`, no data) with a token field kept only in JS memory;
  - `GET /admin/api/stats` requires `X-Admin-Token` (`hmac.compare_digest`) and returns 404 for a missing or wrong token, **and when `ADMIN_TOKEN` is unset**;
  - the payload has turns, average cost per answer, total cost, topic counts (top 10), top 3 products, `since`, model and the price-source date.

  This refines D20: a browser navigation cannot send a header, and a token in the URL would land in Cloud Run request logs, so the 404 guard sits on the data API. D20 gets an amendment line.
- **Deploy prep:**
  - generate a token locally (`secrets.token_urlsafe(32)`);
  - write it to `.env` as `ADMIN_TOKEN`;
  - create the secret `admin-token` via stdin; grant the accessor role to `emporio-agent-sa` only;
  - verify by hash, never print the value.

  It is deployed in S7.

**✅ C8b:**
- `tests/http/test_admin.py`, offline with the fake model:
  - no token → 404; wrong token → 404; token unset → 404;
  - with the right token, after 3 scripted turns, the average cost equals the hand-computed value from the fake usage;
  - topics follow the tools;
  - the top 3 follows the card counts (a 4th product with fewer cards is excluded);
  - a sentinel string from the customer message does not appear in `repr(metrics.__dict__)` or in the JSON.
- Mutations: a token check that always passes; the message stored in the collector; cost without thinking tokens; top 4 instead of 3. Each must be caught.

### S7 · Testing & hardening, documented (≈3 h) [OFF + URL] → C9 — D21
**Does:**
- **Dependencies:** `playwright` pinned in `requirements-dev.txt`, using the browsers already cached.
- **Fake model:** `FakeLLM`/`call`/`say` move from `tests/http/test_chat_api.py` to `tests/fakes.py`, imported by both suites. It is still labeled as a mock.
- **E2E (`tests/e2e/`, offline):** a fixture starts uvicorn on a free port in a thread, with `create_app(settings, llm=FakeLLM(script))`. Two isolated browser contexts.
  - Context 1: Takamine → PIX. Card prices equal the DTO; one avatar per turn.
  - Context 2: order 8 as a visitor → selector → profile B → "não há pedido" → switch to A → the order data appears.
  - Forced failures via the fake model: 503 and 504 show "Tentar novamente" and keep the draft, and the retry succeeds; 429; an empty catalog result; 410 after `DELETE /api/session`.
  - Waits are on visible state only: no `networkidle`, no sleeps.
- **Hardening** (TDD, a test and a mutation each):
  - security-header middleware:
    - `Content-Security-Policy: default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`;
    - `X-Content-Type-Options: nosniff`;
    - `Referrer-Policy: no-referrer`;
    - `Cache-Control: no-store` on `/api/*` and `/admin/api/*`;
  - a request body limit of 16 KiB → 413 `payload_too_large`, checked on `Content-Length` and on the streamed body;
  - unhandled exceptions → a generic 500 JSON without a stack trace (a test with a fake model that raises);
  - `/admin` is not linked from `/` (a test greps the page);
  - `/docs` and `/openapi.json` → 404;
  - the cookie has `HttpOnly`, `SameSite=Lax`, and `Secure` behind https.
- **Rate limit and daily cap:** exercised locally with low limits in the test settings, not in a hosted test revision (that would cost money for no added evidence; this is my call, recorded in the QA report).
- **Deploy (authorized for this project in S4):**
  - redeploy with `ADMIN_TOKEN=admin-token:1` added to `--set-secrets`;
  - label it with the commit;
  - then run on the URL: `/health`, milestone 1, `/admin/api/stats` without a token → 404, with the token → 200, and the headers present.
- **QA report** in `docs/qa/README.md`: one row per case (id, steps, expected, observed, verdict, screenshot link).
  - **Hosted customer flows**, from `scripts/qa_capture.py` with Playwright against the URL (real Gemini, about 15 turns ≈ US$ 0.03):
    - discovery;
    - Takamine → PIX;
    - order (visitor → A → B);
    - return;
    - out of scope;
    - hand-off;
    - `/admin`.
  - **Forced failures** come from the local app with the labeled fake model.
  - Screenshots are named `docs/qa/screens/NN-scenario-viewport.png`, at 320, 390 and 1280 px.
  - The report lists what was **not** verified.

**✅ C9:**
- `pytest` (unit + http + e2e) is all green, citing the literal line; expected about 97 + about 35 new tests;
- `mutation_check.py` → all caught (30 + about 9 new);
- the new revision label equals HEAD;
- the hosted milestone 1 is 219900 → 208905;
- the QA report has no blank verdict.

**🐞 Expected trouble:**
- CSP blocks the fonts or the JSON → read the console errors captured by Playwright.
- The body limit breaks the TestClient → test with a raw `Content-Length`.

### S8 · Capture, review, delivery (Tue 03/11, done by 20:00 SP) [URL] → C10
1. **8.1 Capture.** `scripts/capture_examples.py` drives the hosted URL and writes 5 conversations to `examples/NN-*.md`:
   - discovery (nylon up to R$ 800);
   - promotion + PIX (Kalani);
   - authorized order (A/8);
   - return (online, with the delivery date);
   - out of scope (amplifier + bass).

   Each file has the PT-BR text with an English translation, model, revision, commit, `dataset_id`, tools, public ids, duration and a screenshot. Any blocker → fix the cause, redeploy and capture again.
2. **8.2 Review.** `/qa-response` on each conversation, against the tool results and the manual sections, with no personal data. The verdicts go in `examples/README.md`.
3. **8.3 Final README.** Setup, architecture summary, decisions (linking D1–D21), the cost summary (linking `evals/cost-model.md`), tests and QA, `/admin` (the token is not in the repo), and limitations:
   - the model shutdown on 2027-05-07;
   - the in-memory sessions and metrics;
   - retrieval paraphrases at 4/6;
   - the past estimate of order 8;
   - §3 × §3.1.

   Plus AI usage, the URL and the revision.

   **Clean clone:** `git clone` into the scratchpad → venv → `import_snapshot.py --source <ZIP>` → `build_policy_index.py` → `pytest` → uvicorn → milestone 1 locally.
4. **8.4 Delivery PDF.**
   - The source `docs/delivery/report.html` is in English and committed.
   - `scripts/build_pdf.py` uses Playwright `page.pdf()` to write `Breno Zamponi - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf`. It is git-ignored and handed to Breno.
   - Sections: problem → solution → architecture → guardrails → evidence (tests, mutations, QA, examples) → **cost** (per answer, per type, monthly 500/2k/10k, Cloud Run, BRL) → limitations → links.
   - Plus `docs/delivery/email-reply.md`, the text of the e-mail reply.

**✅ C10:**
- 5/5 conversations without a blocker;
- `check_staged.py` PASS;
- `git ls-remote` == HEAD == the Cloud Run label;
- the last commit before 23:59 SP;
- the PDF opens and has the cost numbers equal to `evals/cost-model.md`;
- Breno uploads it to the form and replies to the e-mail.

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
