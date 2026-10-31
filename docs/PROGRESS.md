# Progress

> Working file with the state of the **current** session, updated at every step.

## ▶️ RESUME HERE — 2026-10-31, ~15:30 America/Campo_Grande (19:30 UTC) — before a /compact

**Repository state:** tree clean · HEAD = the commit `chore: checkpoint before compact (S5 benchmark done)` (check with `git log -1`; must equal `git ls-remote origin refs/heads/main`) · locks: none · background runs: none (the S5 benchmark finished; raw output in `evals/benchmark/*.jsonl`).

**World state (measured 2026-10-31 ~19:05):** Cloud Run `emporio-agent` serves revision `emporio-agent-00002-8wx`, label `commit=37c5597`, `GEMINI_MODEL=gemini-3.1-flash-lite`. URL https://emporio-agent-669786539213.southamerica-east1.run.app. `/health` → 200 with dataset `1412d32a6eeb`. Billing linked; budget `emporio-demo-cap` R$ 30. No CI in this project (gates run locally).

**Current objective:** close S5 with the measured cost model (D19), then S6 (UI), S6b (`/admin`, D20), S7 (testing and hardening with a documented QA report and screenshots, D21; second revision) and S8 (real capture, final README, delivery PDF) before the freeze on **Tue 2026-11-03 23:59 São Paulo**. First plan these sessions in detail (phases, checkpoints with expected numbers) in `docs/SESSIONS.md`, then build them.

**S5.2 closed 2026-10-31 ~17:30 SP (C7b); S5.3 closed ~19:00 SP (C7c, D22); S6 closed ~20:15 SP (C8).** Next: S6b (`/admin`, D20). The local server code is ahead of the Cloud Run revision (`37c5597`) until the S7 redeploy. The original S5.2 instruction, kept for the record:

**Former next step (S5.2):** write `scripts/cost_model.py`. It reads `evals/benchmark/2026-10-31-*.jsonl` and `evals/pricing.json` and writes `evals/cost-model.md` with:
- the average cost per answer and per turn type for `gemini-3.1-flash-lite` (pinned) and `gemini-3.5-flash-lite` (migration path);
- a monthly projection for 500 / 2,000 / 10,000 conversations, with turns per conversation stated as an assumption (e.g. 4) plus a sensitivity line;
- Cloud Run as a separate line, from the official Cloud Run pricing page fetched that day.

Expected for `3.1-flash-lite`: an average of about **US$ 0.00167 per turn** (benchmark summary). Then S5.3: fix the prompt so the out-of-scope question also queries the catalog for the in-scope part (the bass), and rerun only that scenario twice with `3.1-flash-lite`.

**Checkpoints:**

| C | Closes when | State |
| --- | --- | --- |
| C0 | Plan recorded | ✅ `fde18b1` |
| C1 | Import + quote = oracles | ✅ `99baaa2`, `6b08e6e` |
| C2 | SQL executor blocks every violation class | ✅ `6059b51` |
| C-EN | Repository in English | ✅ `258e9a0` |
| C3 | Milestone 1 with real Gemini | ✅ `c717ae5` |
| C4 | Orders bound to the session | ✅ `cb7543a` |
| C5 | Policy retrieval ≥10/12 | ✅ 12/12 base, `cb7543a` |
| C6 | First Cloud Run revision | ✅ rev `00002-8wx` / `37c5597` |
| C7 | Benchmark pins `GEMINI_MODEL` | ✅ `gemini-3.1-flash-lite` ([report](../evals/model-benchmark.md)) |
| C7b | Cost model for the PDF (D19) | ✅ delivered version: 0.00185 USD/turn; 2,000 conversations × 4 turns ≈ US$ 15.47/month incl. Cloud Run gross ([report](../evals/cost-model.md)) |
| C7c | S5.3 guards (D22): no invented products, false absences or promises | ✅ rerun 18/18 turns, 0 blockers, 0 quality notes on both lite models ([report](../evals/model-benchmark.md)) |
| C8 | UI at 320/390/desktop | ✅ local, real Gemini: card R$ 2.199,00 = DTO 219900 → R$ 2.089,05 = DTO 208905 at 320/390/1280, 0 px horizontal overflow, 0 console errors, 1 avatar per turn; order flow visitor → B (no leak) → A ([screens](qa/screens/)) |
| C8b | `/admin` with token, aggregates only (D20) | ⬜ |
| C9 | Playwright + failures + QA report with screenshots (D21), second revision | ⬜ |
| C10 | 5 real conversations, README, clean clone, PDF | ⬜ |

**Re-read, in this order:**
1. `CLAUDE.md` — inviolable rules, language (D16), GCP boundary, freeze.
2. This block.
3. `docs/SESSIONS.md` — sections S5 (cost model), S6, S7, S8 and Risks.
4. `docs/DECISIONS.md` — D11–D19, especially D13 (blockers), D14 (model), D16 (language), D17 (delivery PDF), D19 (cost).
5. `evals/model-benchmark.md` and `evals/pricing.json` — the numbers the cost model uses.
6. Skills: `software-build` (session protocol); `frontend-design` + `frontend-e-ux` for S6; `webapp-testing` + `testes-que-provam` for S7; `qa-response` (explicit `/qa-response`) and `evidencia` for S8; `nuvem-e-deploy` before any redeploy.
7. Code for S6: `app/static/index.html` (minimal page to replace), `app/contracts.py` (DTO), the brand guide at `_private_inputs/guides/01-branding/01_BRANDING.md` with `assets/`, and the mockup at `_private_inputs/visual-references/ui-opcao-1-emporio_mockup.png`.

**Decisions from the conversation (and where they are written):**
- Freeze Tue 2026-11-03 23:59 São Paulo — Breno — D11.
- English repo; customer-facing agent and UI in PT-BR — Breno — D16.
- Delivery: English PDF via Google Forms plus an e-mail reply — Breno — D17.
- Budget US$ 5 → R$ 30; keep the current Gemini key — Breno — D12, D18.
- `businesscardscanner-504717` unlinked from billing — Breno — D18 (re-link after the demo).
- Benchmark candidates revised to 3.1-flash-lite / 3.5-flash-lite / 3.6-flash — Breno — D14.
- Measured cost model in the PDF — Breno — D19.
- Never use the `altivaserra` GCP project — Breno — `CLAUDE.md`, D8.
- `/admin`: topics not raw text, in-memory since instance start, token in Secret Manager — Breno — D20.
- Testing and hardening session with a QA report and organized screenshots — Breno — D21.
- ChatGPT was used for brainstorming and specs — Breno — `docs/ai-usage.md`.

**Do not forget (lives only here or is easy to miss):**
- **Benchmark (2026-10-31):** 0 blocker turns in 54 for all 3 models.
  - Median latency: lite 1.85 s, 3.5-lite 1.62 s, 3.6-flash 6.66 s.
  - Cost per turn (USD): 0.00167, 0.00224 and 0.00900 (baseline; after the S5.3 guards the lite models cost 0.00185 and 0.00241).
  - Average input tokens per turn: about 6.1k (lite), mostly the tool schema and system prompt.
- **Model shutdown:** `gemini-3.1-flash-lite` shuts down on 2027-05-07; `gemini-3.6-flash` prices double on 2027-01-01. Both belong in the PDF's cost section and the README limitations.
- **Retrieval limits:** paraphrases 4/6 and mixed coverage 8/9 ([evals](../evals/policy-retrieval.md)).
- **Order 8's estimate (2026-02-28) is in the past:** answers must call it "a previsão registrada".
- **gcloud:** `altivaserra` is the active `default` configuration. Always use `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio --project emporio-da-musica-agent`. The deploy command is in commit `37c5597`'s S4 history: `gcloud run deploy emporio-agent --source . --region southamerica-east1 --service-account emporio-agent-sa@emporio-da-musica-agent.iam.gserviceaccount.com --allow-unauthenticated --min-instances 0 --max-instances 1 --concurrency 20 --timeout 60 --memory 512Mi --set-secrets GEMINI_API_KEY=gemini-api-key:1 --set-env-vars GEMINI_MODEL=gemini-3.1-flash-lite,EXPOSE_TRACE=1,MAX_TURNS_PER_DAY=400 --labels app=emporio-agent,commit=<sha> --quiet`.
- **Hosted health:** use `/health`; `/healthz` is reserved by Cloud Run (ERRORS class 3).
- **Before every commit:** `git add`, then `.venv/bin/python scripts/check_staged.py` must print PASS. Run `scripts/mutation_check.py` after changing rules (30/30 now) and add a mutation for every new rule.
- **Snapshot tests** read `_private_inputs/challenge`. The ZIP is in `_private_inputs/originals/`.

**Depends on Breno:**
- Nothing blocking S5–S7. Creating the `admin-token` secret (S6b) is covered by the S4 authorization for this project (no new billable product).
- Before S8: he submits the PDF on Google Forms and replies to the e-mail; deploys already authorized for this project (S4). Ask again only for new billable resources.

**Risks of the next steps:**
- A redeploy (S7) costs cents; billing and budget are in place.
- Gemini calls in S6–S8 count against the R$ 30 budget; spend so far is a few cents.
- The final capture (S8) must use the deployed revision and record its commit.

**Before trusting this block, check:**
- `git status --short` is empty and `git log -1 --format=%s` = `chore: checkpoint before compact (S5 benchmark done)`; `git rev-parse HEAD` = `git ls-remote origin refs/heads/main`.
- `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio gcloud run services describe emporio-agent --project emporio-da-musica-agent --region southamerica-east1 --format='value(status.latestReadyRevisionName,metadata.labels.commit)'` → `emporio-agent-00002-8wx 37c5597`.
- `curl -s https://emporio-agent-669786539213.southamerica-east1.run.app/health` → `"status":"ok"`.
- `.venv/bin/python -m pytest -q` → `97 passed`.

## Proofs

| Proof | Command | Result (literal) | When |
| --- | --- | --- | --- |
| First commit published | `git ls-remote origin refs/heads/main` | `00e9e7f665d89e783febedafd7d7908382d82c05` (== HEAD == API) | 2026-10-31 |
| Domain + tools tests | `.venv/bin/python -m pytest -q` | `62 passed in 0.26s` | 2026-10-31 |
| Mutation net | `.venv/bin/python scripts/mutation_check.py` | `15/15 mutations caught` | 2026-10-31 |
| Full suite (offline, fake model) | `.venv/bin/python -m pytest -q` | `76 passed` | 2026-10-31 |
| Mutation net incl. agent/API | `.venv/bin/python scripts/mutation_check.py` | `23/23 mutations caught` | 2026-10-31 |
| Milestone 1, real Gemini | `scripts/smoke_gemini.py --model gemini-3.5-flash` / `gemini-3.1-flash-lite` | `"passed": true` for both ([evals](../evals/milestone1-smoke.md)) | 2026-10-31 |
| Local server | `uvicorn app.main:get_app --factory` + `curl /healthz` | `{"status":"ok","dataset_id":"1412d32a6eeb",...}` | 2026-10-31 |
| Suite after S3 | `.venv/bin/python -m pytest -q` | `95 passed` | 2026-10-31 |
| Mutation net after S3 | `.venv/bin/python scripts/mutation_check.py` | `29/29 mutations caught` | 2026-10-31 |
| Retrieval | `.venv/bin/python scripts/eval_retrieval.py` | `base top-3: 12/12 · paraphrase top-3: 4/6 · mixed coverage: 8/9 sections` | 2026-10-31 |
| Real scenarios (order, hand-off, return) | `scripts/smoke_scenarios.py gemini-3.1-flash-lite` | next_action `choose_profile`, `clarify`, `contact_store`, `clarify`; no fallback ([jsonl](../evals/smoke/2026-10-31-s3-scenarios-gemini-3.1-flash-lite.jsonl)) | 2026-10-31 |
| Hosted health | `curl $URL/health` | `{"status":"ok","dataset_id":"1412d32a6eeb","model":"gemini-3.1-flash-lite"}` 200 | 2026-10-31 |
| Hosted milestone 1 | curl with a cookie jar on `$URL/api/chat` | `95 219900` (2305 ms), then `95 219900 208905 pix` (1917 ms) | 2026-10-31 |
| Hosted no-session | `POST /api/chat` without a cookie | `410 session_expired` | 2026-10-31 |
| Cost model (C7b) | `.venv/bin/python scripts/cost_model.py` | `gemini-3.1-flash-lite: mean 0.00167 USD/turn · 2,000 conversations × 4 turns → Gemini 13.37 USD/month, Cloud Run gross 0.63` (baseline turns; superseded by the S5.3 rerun: 0.00185, 14.81, 0.66) | 2026-10-31 |
| Suite + mutations after S5.2 | `pytest -q` · `mutation_check.py` | `102 passed` · `33/33 mutations caught` | 2026-10-31 |
| Guards rerun (S5.3) | `benchmark_models.py --models gemini-3.1-flash-lite --repeat 2 --tag=-s53` | `"blocker_turns": 0, "quality_issues": 0`, `avg_cost_usd_per_turn 0.00185` (3.5-flash-lite: 0, 0, 0.00241) | 2026-10-31 |
| Suite + mutations after S5.3 | `pytest -q` · `mutation_check.py` | `120 passed` · `42/42 mutations caught` | 2026-10-31 |
| UI (C8) | Playwright on the local app with real Gemini, 320/390/1280 | card `R$ 2.199,00` (DTO 219900) then `R$ 2.089,05` (DTO 208905) at each width; `h_overflow_px 0`; `console_errors []`; turns 1.8–2.4 s | 2026-10-31 |
| Suite + mutations after S6 | `pytest -q` · `mutation_check.py` | `121 passed` · `45/45 mutations caught` | 2026-10-31 |
| Importer | `.venv/bin/python scripts/import_snapshot.py` | `"dataset_id": "1412d32a6eeb"`, counts 9/65/25/50/20/22, `sellable_count` 61 | 2026-10-31 |
