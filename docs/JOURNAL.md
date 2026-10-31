# Journal

> One entry per session, newest first. Each entry covers what was done, what was decided and why, and what was learned. Entries before 2026-10-31 evening were written in Portuguese and translated here.

## 2026-10-31 — S2–S4: agent, orders, policies and a live demo

**Done.**
- Built the Gemini tool loop with server-side checks of prices and claimed actions, the session and the public errors.
- Bound orders to the session's demo profile, built the manual index and BM25 retrieval, and prepared hand-offs.
- Deployed to Cloud Run.
- Milestone 1 passes locally with both candidates and on the public URL.
- Gates: 97 tests and 30/30 mutations.

**Decided.**
- Breno:
  - authorized the deploy and a R$ 30 budget;
  - unlinked `businesscardscanner-504717` to free a billing slot (D18);
  - asked for the measured cost model in the PDF (D19).
- Agent:
  - added a process-wide daily turn cap, because the URL is public and the budget only alerts;
  - kept the hosted health check at `/health`.

**Found.**
- The real model initially jumped to a complaint hand-off on an order question and said "com certeza" before asking the delivery date; two prompt rules fixed both.
- `/healthz` is reserved on Cloud Run (ERRORS class 3).
- Retrieval: paraphrases 4/6, mixed 8/9.

**Not verified.** The benchmark and the cost model (S5); the browser UI at mobile widths (S6).

**Next.** S5 benchmark with the official price list.

## 2026-10-31 — S1 and S-EN: deterministic core tested, repository switched to English

**Done.**
- Pinned dependencies from a clean venv.
- Built the importer (ZIP or directory, NFC-normalized file lookup, full validation, atomic publish, manifest with `dataset_id 1412d32a6eeb`).
- Implemented the pricing and installment rules in cents and the restricted catalog SQL executor.
- Verified the tests with a 15-mutation net: 62 tests pass and 15/15 mutations are caught.
- Translated the whole repository to English.

**Decided.**
- Breno: the deadline is Tue 2026-11-03 23:59 São Paulo time (D11); English everywhere except the customer-facing agent and UI (D16); delivery via a PDF on Google Forms plus an e-mail reply (D17).
- Agent: installments where §3 and §3.1 diverge return `needs_confirmation`; the discovery intent re-applies availability and the customer's stated budget in code.

**Found.** Two mutations escaped and one test was vacuous (error class 1). The first-round deadline recommendation lacked the calendar math (error class 2).

**Not verified.** No Gemini generation call yet.

**Next.** S2: the agent loop and milestone 1 with real Gemini.

## 2026-10-31 — S0: environment ready, inputs audited, public repository

**Done.**
- Organized the inputs in a private ignored folder and created `.venv` with Python 3.12.3.
- Recomputed the reference values from the CSVs, with 0 differences.
- Installed three skills with blobs checked against the pinned commits.
- Created the dedicated GCP project and pushed the first commit.

**Decided.**
- Breno: use a new GCP project, never `altivaserra`.
- Agent, as a recommendation to Breno: third-party skills stay out of Git because of the ambiguous `qa-response` license; continuity documents live in `docs/`.

**Found.** 11 discrepancies and gaps in the data and manual, and 4 in the supporting materials ([findings](source-findings.md)). The most relevant to the code is the §3 × §3.1 installment conflict.

**Not verified.** Whether the current Claude Code session discovered the project skills.

**Next.** Planning with Breno.
