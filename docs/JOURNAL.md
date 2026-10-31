# Journal

> One entry per session, newest first. Each entry covers what was done, what was decided and why, and what was learned. Entries before 2026-10-31 evening were written in Portuguese and translated here.

## 2026-10-31 (after the compact) — S5.2–S7: cost model, anti-invention guards, UI, /admin, QA

**Done.**
- Cost model from the measured turns: US$ 0.00185 per answer on the delivered version, about US$ 15.47 a month for 2,000 conversations including Cloud Run (gross).
- Server-side guards (D22): product references, promises, false absences, string type, fetch-on-correction.
- Ressonância UI with local fonts and a vector mark.
- `/admin` with aggregates only (D20).
- Hardening layer and 13 browser tests.
- Two new revisions; hosted QA 12/12 on `00004-8vj`.
- Gates: 152 tests, 58/58 mutations.

**Decided.**
- Breno: avoid invented products, numbers or hallucination at any cost; the agent turned that into D22.
- Agent:
  - the `/admin` 404 guard sits on the data API (D20 amendment);
  - the cost model uses the delivered-version turns, not the first baseline;
  - rate-limit and daily-cap checks stay local (cost, no added evidence).

**Found.**
- Reading the real tool arguments, not only the answers, showed what the first battery missed:
  - an invented model ("Ibanez GSR200");
  - two false "we don't have it" answers caused by a `status` column trap (ERRORS class 4);
  - a nylon search that would offer a steel guitar (ERRORS class 1).
- Looking at the screens found an invented "à vista" label on cards.
- The pre-commit scan crashed on the first binary files.
- I wrote UTC-shifted times in `PROGRESS.md` (ERRORS class 2).
- The first hosted QA run failed one case (the out-of-scope question got a preference question instead of options); fixed in the prompt, measured 10/10, redeployed.

**Not verified.** Real phones and screen readers; rate limits on the URL; a real instance recycle (see the [QA report](qa/README.md) §4).

**Next.** S8: capture 5 real conversations on the URL, `/qa-response`, final README, clean-clone reproduction, delivery PDF and e-mail text.

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
