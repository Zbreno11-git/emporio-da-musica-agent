# Progress

> Working file with the state of the **current** session, updated at every step.

## ▶️ RESUME HERE — 2026-10-31 17:50 São Paulo (mid-S8, before a /compact)

**Repository state:**
- Tree clean; HEAD = the commit `chore: checkpoint before compact (S8 capture taken on 00006-z4v, QA 12/12)` (`03ddb29` or the docs commit right after it). Check `git log -1` against `git ls-remote origin refs/heads/main`.
- Locks: none. Background runs: none. The local uvicorn on port 8765 was stopped.
- The 5 example `.md` files are **not** committed on purpose: `scripts/capture_examples.py --rerender` rebuilds them from `examples/raw/`.

**World state (measured 2026-10-31 17:49 SP):**
- **Cloud Run:** `emporio-agent` serves **`emporio-agent-00006-z4v`**, label `commit=0756d26`, secrets `GEMINI_API_KEY=gemini-api-key:1` and `ADMIN_TOKEN=admin-token:1`. `/health` ok.
- **Hosted QA:** `scripts/qa_capture.py` → `12/12 hosted cases passed` on `00006-z4v`.
- **Captures:** the 5 delivery conversations were captured on `00006-z4v`, 5/5 checks pass (`examples/raw/*.json`, `examples/screens/*.png`).
- **Spend:** billing linked; budget R$ 30; Gemini spend so far a few cents.

**Current objective:** finish S8 and close C10 before the freeze on **Tue 2026-11-03 23:59 São Paulo**. Breno asked (2026-10-31 17:49) to plan and build what is left **and fix every open debt or bug**.

**Open debts and bugs — fix first, in this order (each with a test and a mutation when it is a rule):**
1. **`HEAD /` and `HEAD /health` answer 405.** Uptime checkers use HEAD.
   - Fix: route GET+HEAD (`@app.api_route(..., methods=["GET", "HEAD"])`) for `/`, `/health`, `/healthz`, `/admin`.
   - Test: `tests/http/test_hardening.py`.
2. **Policy sources disappear on follow-up turns.** In `examples/raw/04-return-policy.json`, turn 2 applies §4.1, which was retrieved in turn 1 and sits in the history, but `sources` is empty, so the UI shows no "Fontes".
   - Recommended fix: the session keeps the policy sources of the previous turn. A turn **without tool calls** whose text survives the checks re-lists them, labeled "(consultada na mensagem anterior)". The `Source` contract needs no new field.
   - Test in `tests/http/test_chat_api.py` (two turns: `search_policy` then text only); mutation.
   - If this turns out wrong for small talk ("obrigado"), list it as a README limitation instead and tell Breno.
3. **After 1–2:** redeploy (command below, label = HEAD), then `scripts/qa_capture.py` (expect 12/12), then **recapture** `scripts/capture_examples.py` (expect 5/5). `examples/` must be real captures of the delivered revision.
4. **Translations:** write `examples/translations.json` (exact PT string → EN) for every customer and agent text in `examples/raw/*.json`, then `--rerender` until it prints `translations pending: 0` for all 5.
5. **Review (S8.2):** `examples/README.md` with one section per conversation, applying the rubric of `.claude/skills/qa-response/SKILL.md` (read it; the skill has `disable-model-invocation`, so apply it by hand and say so).
   - For each claim that changes a decision: the fact, the source (tool result / manual section), and a verdict (sustained / contradicted / no evidence).
   - Points already seen: 03 mixes "tu"/"você" (language note); 01 turn 2 is generic but supported; 04 turn 2 is sustained by §4.1 (refund in up to 10 business days, return shipping paid by the store, original packaging).
   - Any blocker → fix the cause, redeploy, recapture.
6. **Update `docs/ai-usage.md`** with the real use in these sessions: Claude Code built and verified; Breno decided scope and money; ChatGPT for brainstorming and specs.

**Then the deliverables:**
7. **Final `README.md` (English).** It covers:
   - what it is;
   - the live URL and revision;
   - a quick tour;
   - architecture (one diagram or list);
   - guardrails (D22);
   - setup from scratch: venv, `requirements-dev`, `playwright install chromium`, `import_snapshot.py --source <challenge ZIP>`, `build_policy_index.py`, `.env` from `.env.example` (note `ADMIN_TOKEN`), pytest, uvicorn;
   - tests/QA links; cost summary (`evals/cost-model.md`); `/admin`;
   - decisions (link D1–D22);
   - limitations, including the 2027-05-07 model shutdown, in-memory sessions and metrics, retrieval paraphrases 4/6, the order 8 estimate in the past, §3 × §3.1, rate limits only tested locally, and characteristics outside the quality list being prompt-governed;
   - AI usage.
8. **Clean clone (C10):** `git clone https://github.com/Zbreno11-git/emporio-da-musica-agent` into the scratchpad. Follow the README literally with the ZIP from `_private_inputs/originals/` and run `pytest` plus milestone 1 locally. Fix the README until it works as written.
9. **Delivery PDF (D17):**
   - `docs/delivery/report.html` (English, committed) → `scripts/build_pdf.py` (Playwright `page.pdf()`, A4) → `Breno Zamponi - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf`. It is git-ignored (`*.pdf`); hand the path to Breno.
   - Sections: problem → solution → architecture → guardrails (D22, with the real cases) → evidence (tests 156+, mutations 60/60, hosted QA 12/12, 5 examples) → **cost** (US$ 0.00203 per answer; per turn type; monthly 500/2,000/10,000 with Cloud Run and BRL; model lines and the 2027 dates) → limitations → links (repo, URL, examples, QA).
   - Every number is read from `evals/cost-model.md`, `docs/qa/README.md` and the raw files, not typed from memory.
   - Also `docs/delivery/email-reply.md` (short, English, with the repo link).
10. **Close C10:**
    - `check_staged.py` PASS;
    - `git ls-remote` == HEAD;
    - Cloud Run label == last code commit;
    - JOURNAL entry; this block updated;
    - tell Breno what he must do (upload the PDF to the Google Form, reply to the e-mail, re-link `businesscardscanner-504717` after the evaluation).

**Checkpoints:** C0–C9 ✅ (C9: 156 tests, 60/60 mutations, hosted 12/12). C7b cost model ✅ on the delivered version (`-s8` runs). **C10 ⬜**: 5 real conversations reviewed without blockers, README, clean clone, PDF.

**Re-read, in this order:**
1. `CLAUDE.md`.
2. This block.
3. `docs/SESSIONS.md` S8.
4. `docs/DECISIONS.md` D13, D16, D17, D19–D22.
5. `docs/qa/README.md`.
6. `evals/cost-model.md`.
7. `examples/raw/*.json`.
8. `.claude/skills/qa-response/SKILL.md`.
9. Skills: `software-build`, `evidencia` (every number in the README/PDF), `frontend-e-ux` (the PDF is a visual artifact: look at it rendered), `nuvem-e-deploy` (before the redeploy).

**Decisions from the conversation (and where they are written):**
- Freeze Tue 2026-11-03 23:59 São Paulo — Breno — D11.
- English repo; customer-facing agent and UI in PT-BR — Breno — D16.
- Delivery: English PDF via Google Forms plus an e-mail reply — Breno — D17.
- Budget US$ 5 → R$ 30; keep the current Gemini key — Breno — D12, D18.
- `businesscardscanner-504717` unlinked from billing — Breno — D18 (re-link after the demo).
- Benchmark candidates 3.1-flash-lite / 3.5-flash-lite / 3.6-flash — Breno — D14.
- Measured cost model in the PDF — Breno — D19.
- Never use the `altivaserra` GCP project — Breno — `CLAUDE.md`, D8.
- `/admin`: aggregates only, token in Secret Manager — Breno — D20 (guard on the data API: agent amendment, in D20).
- Testing and hardening with a QA report and screenshots — Breno — D21.
- No invented products, numbers or qualities "a todo custo", enforced by the server — Breno (goal), agent (mechanism) — D22.
- 2026-10-31 17:49: plan and build the rest **and fix every open debt or bug** — Breno — this block.
- ChatGPT used for brainstorming and specs — Breno — `docs/ai-usage.md`.

**Do not forget (lives only here or is easy to miss):**
- **Costs for the PDF:** US$ 0.00203 per answer on the delivered version (`evals/cost-model.md`, `-s8` runs). Earlier runs: 0.00167 (baseline), 0.00185 (S5.3). For 2,000 conversations × 4 turns: US$ 16.24 Gemini + US$ 0.65 Cloud Run gross = US$ 16.89 ≈ R$ 91,58 at PTAX 5.4212 (2026-10-30).
- **Model dates:** `gemini-3.1-flash-lite` shuts down on 2027-05-07 (replacement `gemini-3.5-flash-lite`: 0 blockers, US$ 0.00255 per turn). `gemini-3.6-flash` prices double on 2027-01-01.
- **D22 real cases**, for the PDF and README:
  - invented "Ibanez GSR200";
  - `status = 'available'` → false "we don't have it";
  - a nylon search without the filter would offer a steel Shelby;
  - a PIX price computed by the model;
  - "posso ficar de olho";
  - "timbre bem definido" not in the data (≈ 8% of 126 answers).
- **Times:** headless Chromium renders UTC unless `timezone_id` is set. Read times with `TZ=America/Sao_Paulo date` (ERRORS class 2).
- **Deploy command** (authorized for this project since S4): `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio gcloud run deploy emporio-agent --project emporio-da-musica-agent --source . --region southamerica-east1 --service-account emporio-agent-sa@emporio-da-musica-agent.iam.gserviceaccount.com --allow-unauthenticated --min-instances 0 --max-instances 1 --concurrency 20 --timeout 60 --memory 512Mi --set-secrets GEMINI_API_KEY=gemini-api-key:1,ADMIN_TOKEN=admin-token:1 --set-env-vars GEMINI_MODEL=gemini-3.1-flash-lite,EXPOSE_TRACE=1,MAX_TURNS_PER_DAY=400 --labels app=emporio-agent,commit=<short HEAD> --quiet`.
- **Shell traps:**
  - `pkill -f <pattern>` kills the shell running it; use `fuser -k 8765/tcp`.
  - argparse reads `--tag -s8` as an option; write `--tag=-s8`.
  - The auto-mode classifier blocks editing `CLAUDE.md` from a shell script; use the Edit tool.
- **Before every commit:** `git add`, then `scripts/check_staged.py` must print PASS. It lists images for review by eye and fails on broken relative links (that is why the example `.md` files wait for `examples/README.md`).
- **`.env`** holds `GEMINI_API_KEY` and `ADMIN_TOKEN`. Never print them; verify by hash.
- **Snapshot tests** read `_private_inputs/challenge`. Browser tests need `python -m playwright install chromium` (Chromium v1248 is cached).

**Depends on Breno:** nothing until the end. Then he uploads the PDF to the Google Form, replies to the e-mail, and re-links `businesscardscanner-504717` after the evaluation.

**Risks of the next steps:**
- Each redeploy invalidates the examples. Do the code fixes (debts 1–2) **before** recapturing.
- Gemini spend: ≈ US$ 0.05 per QA + capture round.

**Before trusting this block, check:**
- `git status --short` is empty and `git rev-parse HEAD` = `git ls-remote origin refs/heads/main`.
- `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio gcloud run services describe emporio-agent --project emporio-da-musica-agent --region southamerica-east1 --format='value(status.latestReadyRevisionName,metadata.labels.commit)'` → `emporio-agent-00006-z4v 0756d26`.
- `curl -s https://emporio-agent-669786539213.southamerica-east1.run.app/health` → `"status":"ok"`.
- `.venv/bin/python -m pytest -q` → `156 passed`; `scripts/mutation_check.py` → `60/60 mutations caught`.
- `ls examples/raw` → 5 json files; `.venv/bin/python scripts/capture_examples.py --rerender` → 5 × PASS with translations pending (expected until step 4).

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
