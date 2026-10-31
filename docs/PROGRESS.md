# Progress

> Working file with the state of the **current** session, updated at every step.

## ▶️ RESUME HERE — 2026-10-31 19:15 São Paulo (S8 done; C10 waits only for Breno's submission)

**Repository state:** tree clean after the closing commit; HEAD == `origin/main` (check `git log -1` against `git ls-remote origin refs/heads/main`). No locks, no background runs.

**World state (measured 2026-10-31):**
- Cloud Run `emporio-agent` serves **`emporio-agent-00010-x5j`**, label `commit=69f4b68` (the last code commit; later commits are docs only). Secrets `gemini-api-key:1`, `admin-token:1`. `/health` ok; `HEAD /` 200.
- Hosted QA `13/13` on `00010-x5j`; the five delivery conversations captured on it (5/5 checks, reviewed in `examples/README.md`).
- Gates: `200 passed`; `78/78 mutations caught`. Clean clone (README followed literally, challenge ZIP): `dataset_id 1412d32a6eeb`, `200 passed`, `78/78` with `EMPORIO_SNAPSHOT`, milestone 1 `"passed": true`.
- Final benchmark runs (`evals/benchmark/*-s9.jsonl`, `*-s9sec.jsonl`): store scenarios 0 blockers on both models; red-team battery 18 turns, 0 blockers. Cost model: US$ 0.00203 per answer; US$ 16.89 a month for 2,000 conversations (R$ 91,57).
- Delivery PDF built at the repository root (git-ignored): `Breno Zamponi - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf`, from `docs/delivery/report.template.html` by `scripts/build_pdf.py`. E-mail text: `docs/delivery/email-reply.md`.

**Depends on Breno (C10):**
1. Upload the PDF to the Google Form.
2. Reply to the selection e-mail with the text in `docs/delivery/email-reply.md` (repository link).
3. After the evaluation: re-link billing for `businesscardscanner-504717` (D18).

**Freeze:** Tue 2026-11-03 23:59 São Paulo (D11). Any change after this point needs Breno's authorization; a code change means redeploy → `qa_capture.py` → `capture_examples.py` → review → `build_pdf.py`, in that order, because each step's numbers come from the previous one.

**If something must change before the freeze:**
- Deploy command (authorized for this project since S4): `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio gcloud run deploy emporio-agent --project emporio-da-musica-agent --source . --region southamerica-east1 --service-account emporio-agent-sa@emporio-da-musica-agent.iam.gserviceaccount.com --allow-unauthenticated --min-instances 0 --max-instances 1 --concurrency 20 --timeout 60 --memory 512Mi --set-secrets GEMINI_API_KEY=gemini-api-key:1,ADMIN_TOKEN=admin-token:1 --set-env-vars GEMINI_MODEL=gemini-3.1-flash-lite,EXPOSE_TRACE=1,MAX_TURNS_PER_DAY=400 --labels app=emporio-agent,commit=<short HEAD> --quiet`.
- Benchmark files are named by the UTC date (`date.today()` on this machine): a rerun after 21:00 São Paulo writes `2026-11-01-*`, and `scripts/cost_model.py` reads `BENCHMARK_DATE = "2026-10-31"`.
- Shell traps: `pkill -f` kills its own shell (use `fuser -k 8765/tcp`); argparse needs `--tag=-s9`; `| tail` hides a script's exit code; the challenge ZIP name has a decomposed "é" (use a glob); edit `CLAUDE.md` with the Edit tool.
- Before every commit: `git add`, then `scripts/check_staged.py` → PASS.

**Before trusting this block:** `git status --short` empty; `gcloud run services describe ...` → `emporio-agent-00010-x5j 69f4b68`; `curl $URL/health` ok; `pytest -q` → `200 passed`.

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
| Quality guard rerun (S8) | `benchmark_models.py --models ... --repeat 2 --tag=-s8` | 3.1-flash-lite `"blocker_turns": 0`, 0.00203 USD/turn; 3.5-flash-lite 0, 0.00255 | 2026-10-31 |
| Suite + mutations after the quality guard | `pytest -q` · `mutation_check.py` | `156 passed` · `60/60 mutations caught` | 2026-10-31 |
| Hosted QA on `00006-z4v` | `scripts/qa_capture.py` | `12/12 hosted cases passed []` | 2026-10-31 |
| Delivery captures on `00006-z4v` | `scripts/capture_examples.py` | `01..05: PASS` (5/5) | 2026-10-31 |
| Importer | `.venv/bin/python scripts/import_snapshot.py` | `"dataset_id": "1412d32a6eeb"`, counts 9/65/25/50/20/22, `sellable_count` 61 | 2026-10-31 |
| D23 guards and battery | `benchmark_models.py ... --tag=-s9sec` / `--tag=-s9` | attacks 18 turns, 0 blockers; store 36 turns (2 models), 0 blockers | 2026-10-31 |
| Suite + mutations, final | `pytest -q` · `mutation_check.py` | `200 passed` · `78/78 mutations caught` | 2026-10-31 |
| Final revision | `gcloud run services describe ...` | `emporio-agent-00010-x5j 69f4b68`; `HEAD /` 200 | 2026-10-31 |
| Hosted QA on `00010-x5j` | `scripts/qa_capture.py` | `13/13 hosted cases passed []` | 2026-10-31 |
| Delivery captures on `00010-x5j` | `scripts/capture_examples.py` · `--rerender` | `01..05: PASS`; `translations pending: 0` ×5 | 2026-10-31 |
| Clean clone (C10) | README steps in a fresh clone | `dataset_id 1412d32a6eeb`; `200 passed`; `78/78` with `EMPORIO_SNAPSHOT`; smoke `"passed": true` | 2026-10-31 |
| Delivery PDF | `scripts/build_pdf.py` | `wrote docs/delivery/report.html and Breno Zamponi - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf` (4 pages, looked at) | 2026-10-31 |
