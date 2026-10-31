# Progress

> Working file with the state of the **current** session, updated at every step.

## ▶️ RESUME HERE — 2026-10-31 17:40 São Paulo (S7 closed)

**Repository state:** tree clean after the S7 docs commit (check `git log -1`; must equal `git ls-remote origin refs/heads/main`) · locks: none · background runs: none. A local uvicorn on port 8765 may still be running from S6/S6b (`fuser -k 8765/tcp` stops it; no check depends on it).

**World state (measured 2026-10-31 17:31–17:35 SP):**
- **Cloud Run:** `emporio-agent` serves revision **`emporio-agent-00004-8vj`**, label `commit=8589cff`, model `gemini-3.1-flash-lite`.
- **Secrets:** `GEMINI_API_KEY=gemini-api-key:1` and `ADMIN_TOKEN=admin-token:1`.
- **Checks:** `/health` 200; hosted QA 12/12 ([report](qa/README.md)).
- **Billing:** linked; budget `emporio-demo-cap` R$ 30. Gemini spend so far is cents (≈ 200 benchmark and QA turns × ≈ US$ 0.002).

**Current objective:** S8, before the freeze on **Tue 2026-11-03 23:59 São Paulo** (target: done by 20:00 on Nov 3; it can start earlier):
- real capture and review;
- final README and clean-clone reproduction;
- delivery PDF and e-mail text.

**Exact next step (S8.1):** write `scripts/capture_examples.py`, reusing the `Run` helper pattern of `scripts/qa_capture.py`. It captures on the hosted URL the 5 conversations of guide 03 §6 into `examples/NN-*.md`:
1. discovery (nylon ≤ R$ 800, then "e no PIX?");
2. promotion + PIX (Kalani);
3. authorized order (A/8 after choosing the profile);
4. return (online, then give the delivery date);
5. out of scope (amplifier + bass).

Each file holds the PT-BR transcript with an English translation, the revision, commit and dataset, the tools and public ids, the duration and a screenshot. Expected: 5/5 without blockers.

Then S8.2: run `/qa-response` on each conversation, and carry the two observations from `docs/qa/README.md` §4 ("Pode sim!" before the delivery date; "Como te falei").

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
| C7c | S5.3 guards (D22): no invented products, false absences or promises | ✅ rerun 18/18 turns, 0 blockers, 0 quality notes on both lite models |
| C8 | UI at 320/390/desktop | ✅ `a2f604f` |
| C8b | `/admin` with token, aggregates only (D20) | ✅ `ebf4247`; on the URL: no token 404, token 200 |
| C9 | Playwright + failures + QA report with screenshots (D21), second revision | ✅ 152 tests, 58/58 mutations, hosted 12/12 on `00004-8vj` / `8589cff` ([QA](qa/README.md)) |
| C10 | 5 real conversations, README, clean clone, PDF | ⬜ next (S8) |

**Re-read, in this order:**
1. `CLAUDE.md`: inviolable rules, language (D16), GCP boundary, freeze.
2. This block.
3. `docs/SESSIONS.md`: S8 and Risks.
4. `docs/DECISIONS.md`: D13, D16, D17, D19, D20, D22.
5. `docs/qa/README.md` (§4 observations) and `evals/cost-model.md` (numbers for the PDF).
6. Skills:
   - `software-build`;
   - `qa-response` (explicit `/qa-response`) and `evidencia` for S8;
   - `nuvem-e-deploy` before any redeploy;
   - for the PDF, plan `docs/delivery/report.html` → `scripts/build_pdf.py` with Playwright `page.pdf()`.

**Decisions from the conversation (and where they are written):**
- Freeze Tue 2026-11-03 23:59 São Paulo — Breno — D11.
- English repo; customer-facing agent and UI in PT-BR — Breno — D16.
- Delivery: English PDF via Google Forms plus an e-mail reply — Breno — D17.
- Budget US$ 5 → R$ 30; keep the current Gemini key — Breno — D12, D18.
- `businesscardscanner-504717` unlinked from billing — Breno — D18 (re-link after the demo).
- Benchmark candidates revised to 3.1-flash-lite / 3.5-flash-lite / 3.6-flash — Breno — D14.
- Measured cost model in the PDF — Breno — D19.
- Never use the `altivaserra` GCP project — Breno — `CLAUDE.md`, D8.
- `/admin`: topics not raw text, in-memory since instance start, token in Secret Manager — Breno — D20. The guard sits on the data API, an agent amendment written in D20.
- Testing and hardening session with a QA report and organized screenshots — Breno — D21.
- No invented products or numbers "a todo custo", enforced by the server — Breno (goal), agent (mechanism) — D22.
- ChatGPT was used for brainstorming and specs — Breno — `docs/ai-usage.md`.

**Do not forget (lives only here or is easy to miss):**
- **Costs for the PDF:** US$ 0.00185 per answer on the delivered version (`evals/cost-model.md`); the first baseline was 0.00167. For 2,000 conversations × 4 turns: about US$ 14.81 Gemini + US$ 0.66 Cloud Run gross, about R$ 83,85 at PTAX 5.4212 (2026-10-30).
- **Model shutdown and prices:** both go in the PDF and in the README limitations.
  - `gemini-3.1-flash-lite` shuts down on 2027-05-07. Its replacement, `gemini-3.5-flash-lite`, had 0 blockers at US$ 0.00241 per turn.
  - `gemini-3.6-flash` prices double on 2027-01-01.
- **Retrieval limits:** paraphrases 4/6 and mixed coverage 8/9 ([evals](../evals/policy-retrieval.md)).
- **Order 8's estimate (2026-02-28) is in the past:** answers call it "a previsão registrada".
- **Times:** headless Chromium renders UTC unless `timezone_id` is set. Read times from `TZ=America/Sao_Paulo date` or from the commits (ERRORS class 2).
- **gcloud:** `altivaserra` is the active `default` configuration. Always use `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio --project emporio-da-musica-agent`. Deploy command (now with the admin secret): `gcloud run deploy emporio-agent --project emporio-da-musica-agent --source . --region southamerica-east1 --service-account emporio-agent-sa@emporio-da-musica-agent.iam.gserviceaccount.com --allow-unauthenticated --min-instances 0 --max-instances 1 --concurrency 20 --timeout 60 --memory 512Mi --set-secrets GEMINI_API_KEY=gemini-api-key:1,ADMIN_TOKEN=admin-token:1 --set-env-vars GEMINI_MODEL=gemini-3.1-flash-lite,EXPOSE_TRACE=1,MAX_TURNS_PER_DAY=400 --labels app=emporio-agent,commit=<sha> --quiet`. After each deploy, run `scripts/qa_capture.py` on the URL.
- **Hosted health:** use `/health` (`/healthz` is reserved by Cloud Run, ERRORS class 3). `HEAD /` answers 405.
- **Before every commit:** `git add`, then `scripts/check_staged.py` must print PASS. It now handles binaries and lists the images to review by eye. Every new rule gets a mutation (58/58 now).
- **Snapshot tests** read `_private_inputs/challenge`; the ZIP is in `_private_inputs/originals/`. Browser tests need `python -m playwright install chromium`.
- **`.env`** now also holds `ADMIN_TOKEN`. Never print it; verify it by hash.

**Depends on Breno:**
- Nothing blocks S8.1–S8.3.
- At the end, he uploads the PDF to the Google Form and replies to the e-mail.
- After the evaluation, he re-links `businesscardscanner-504717` to billing.

**Risks of the next steps:**
- The capture must use the deployed revision and record its commit. A fix found by the review means redeploying and capturing again.
- Gemini calls count against the R$ 30 budget (cents so far).

**Before trusting this block, check:**
- `git status --short` is empty and `git rev-parse HEAD` = `git ls-remote origin refs/heads/main`.
- `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio gcloud run services describe emporio-agent --project emporio-da-musica-agent --region southamerica-east1 --format='value(status.latestReadyRevisionName,metadata.labels.commit)'` → `emporio-agent-00004-8vj 8589cff`.
- `curl -s https://emporio-agent-669786539213.southamerica-east1.run.app/health` → `"status":"ok"`.
- `.venv/bin/python -m pytest -q` → `152 passed`; `scripts/mutation_check.py` → `58/58`.

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
| Suite + mutations after S6b | `pytest -q` · `mutation_check.py` | `134 passed` · `50/50 mutations caught` | 2026-10-31 |
| Upload set | `gcloud meta list-files-for-upload .` | 38 files; only `evals/pricing.json` from `evals/`; no tests, docs, scripts, `.env` or `_private_inputs` | 2026-10-31 |
| Suite after S7 | `pytest -q` | `152 passed` (13 browser tests) | 2026-10-31 |
| Mutation net after S7 | `mutation_check.py` | `58/58 mutations caught` | 2026-10-31 |
| Second revision | `gcloud run services describe ...` | `emporio-agent-00004-8vj 8589cff` | 2026-10-31 |
| Hosted QA | `scripts/qa_capture.py` | `12/12 hosted cases passed []` ([table](qa/hosted-results.md)) | 2026-10-31 |
| Hosted hardening | curl on the URL | CSP/nosniff/no-referrer/DENY present; `/docs` `/openapi.json` 404; stats 404 without token; 20 KB body `413` | 2026-10-31 |
| Importer | `.venv/bin/python scripts/import_snapshot.py` | `"dataset_id": "1412d32a6eeb"`, counts 9/65/25/50/20/22, `sellable_count` 61 | 2026-10-31 |
