# Progress

> Working file with the state of the **current** session, updated at every step.

## ▶️ RESUME HERE — 2026-10-31 (America/Campo_Grande)

**State:** S0, S0b and S1 closed. S-EN (translation to English) is being committed.

**Exact next step:** S2.2, writing `app/agent.py`. `app/contracts.py` and `app/config.py` already exist as drafts, uncommitted until S2 closes.

**Checkpoints:**

| C | Closes when | State |
| --- | --- | --- |
| C0 | Plan recorded | ✅ `fde18b1` |
| C1 | Import + quote = oracles | ✅ `99baaa2`, `6b08e6e` |
| C2 | SQL executor blocks every violation class | ✅ `6059b51` |
| C-EN | Repository in English | 🔵 |
| C3 | Milestone 1 with real Gemini | ⬜ |
| C4 | Orders bound to the session | ⬜ |
| C5 | Policy retrieval ≥10/12 | ⬜ |
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
- **Contract fixture:** `tests/fixtures/turns.json` is a local copy of the guide-02 examples, not yet tracked; decide in S2 whether to version it, since it has customer-facing PT text and no personal data.

## Proofs

| Proof | Command | Result (literal) | When |
| --- | --- | --- | --- |
| First commit published | `git ls-remote origin refs/heads/main` | `00e9e7f665d89e783febedafd7d7908382d82c05` (== HEAD == API) | 2026-10-31 |
| Domain + tools tests | `.venv/bin/python -m pytest -q` | `62 passed in 0.26s` | 2026-10-31 |
| Mutation net | `.venv/bin/python scripts/mutation_check.py` | `15/15 mutations caught` | 2026-10-31 |
| Importer | `.venv/bin/python scripts/import_snapshot.py` | `"dataset_id": "1412d32a6eeb"`, counts 9/65/25/50/20/22, `sellable_count` 61 | 2026-10-31 |
