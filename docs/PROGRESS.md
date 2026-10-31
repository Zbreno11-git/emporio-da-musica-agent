# Progress

> Working file with the state of the **current** session, updated at every step.

## ▶️ RESUME HERE — 2026-10-31 (America/Campo_Grande)

**State:** S0, S0b, S1, S-EN, S2 and S3 closed. Orders, policies and hand-offs work with real Gemini.

**Exact next step:** S4 is the first deploy and starts with a **mandatory pause**: ask Breno to authorize linking billing to `emporio-da-musica-agent` and creating the BRL budget (≈ US$ 5) before any billable command. Meanwhile, the `Dockerfile` and `.gcloudignore` can be written offline.

**Checkpoints:**

| C | Closes when | State |
| --- | --- | --- |
| C0 | Plan recorded | ✅ `fde18b1` |
| C1 | Import + quote = oracles | ✅ `99baaa2`, `6b08e6e` |
| C2 | SQL executor blocks every violation class | ✅ `6059b51` |
| C-EN | Repository in English | ✅ `258e9a0` |
| C3 | Milestone 1 with real Gemini | ✅ (S2 commit) |
| C4 | Orders bound to the session | ✅ (S3 commit) |
| C5 | Policy retrieval ≥10/12 | ✅ 12/12 base (S3 commit) |
| C6 | First Cloud Run revision | ⬜ |
| C7 | Benchmark pins `GEMINI_MODEL` | ⬜ |
| C8 | UI at 320/390/desktop | ⬜ |
| C9 | Playwright + failures, second revision | ⬜ |
| C10 | 5 real conversations, README, clean clone, PDF | ⬜ |

**Do not forget:**
- **GCP:** gcloud has `altivaserra` as the active `default` configuration. This repo uses `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio` and the project `emporio-da-musica-agent`.
- **Billing:** **not** linked yet (`billingEnabled=False`). Linking it and creating the BRL budget (≈ US$ 5) need Breno's confirmation in S4.
- **Gemini key:** belongs to `gen-lang-client-0041725501`, with active billing on the same account.
- **Freeze:** Tue 2026-11-03 23:59 **São Paulo** time (UTC−3, one hour ahead of Campo Grande).
- **Before every commit:** `git add`, then `.venv/bin/python scripts/check_staged.py` must print PASS.
- **Local `.env`:** has `GEMINI_MODEL=gemini-3.1-flash-lite` as a provisional value until the S5 benchmark.
- **Retrieval limits measured:** 4/6 paraphrases and 8/9 sections on mixed questions ([evals](../evals/policy-retrieval.md)). The model writes the search query and may rephrase; check this again on the real conversations.
- **Prompt changes after the real run:** order answers come before any hand-off; return eligibility asks for the delivery date first.

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
| Importer | `.venv/bin/python scripts/import_snapshot.py` | `"dataset_id": "1412d32a6eeb"`, counts 9/65/25/50/20/22, `sellable_count` 61 | 2026-10-31 |
