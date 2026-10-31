# Journal

> One entry per session, newest first. Each entry covers what was done, what was decided and why, and what was learned. Entries before 2026-10-31 evening were written in Portuguese and translated here.

## 2026-10-31 night — after Breno's own session

**Found.** Breno used the demo and was satisfied with the answers. The request logs (no customer text is logged, D20) showed every chat at 200, but four `GET / 400` from a link-preview bot ("Mozilla/5.0 (compatible)", HTTP/1.1): Starlette answers a malformed or unknown-unit `Range` with 400. Reproduced on the URL, fixed by ignoring `Range` (RFC 9110 allows it), live as `00011-z2g`. Rereading the challenge statement showed the README lacked an explicit technical-decisions section, the assumptions and "with more time"; added. The recapture on `00011-z2g` has two answers with wording notes ("está a caminho" for a shipped order; a return answer that states the deadline only in the team summary); they are reviewed as captured, not recaptured until nicer.

## 2026-10-31 evening (second compact) — S8: debts, LLM-attack hardening (D23), capture, review, README, PDF

**Done.**
- Open debts closed and live: `HEAD` on the page routes (was 405); manual sections carried to the follow-up turn and cited as "consultada na mensagem anterior" when the answer relies on them (capture 04).
- D23, after Breno asked to defend the agent against prompt injection and other LLM attacks: the customer's message is never evidence for a price, discount or deadline; deadlines checked against the manual; false absences rejected; the hand-off summary checked like the shown text; "preparei um resumo" requires a prepared hand-off; prompt rule 13; HTML in model text proven inert in the browser; `docs/security.md` maps OWASP LLM 2025 to controls and tests.
- Red-team battery (9 attacks × 2) and the store scenarios rerun on the final code: 0 blockers. Cost model on those turns: US$ 0.00203 per answer, US$ 16.89 a month for 2,000 conversations.
- Revision `00010-x5j` (commit `69f4b68`): hosted QA 13/13 (new prompt-injection case), five conversations recaptured, translated and reviewed (5 PASS). README rewritten; the clean clone reproduced the dataset, the tests and milestone 1. Delivery PDF built from the generated files; e-mail text ready.
- Gates: 200 tests, 78/78 mutations.

**Decided.**
- Breno: defend against LLM attacks (D23 goal).
- Agent: keep the technical panel on for the evaluators (D23 trigger: off with real customers); the PDF is rendered from a template filled by `scripts/build_pdf.py`, so no number is typed by hand.

**Found.**
- The security review question "who writes each evidence source?" found that customer amounts and percentages counted as evidence (ERRORS class 5).
- The battery found its own blind spots: a first wording of rule 13 broke the exact-R$ 500 hand-off (2/2), and false absences under attack passed string checks (ERRORS class 4). Each became a blocker check in the battery.
- Each capture review found one more gap: an unchecked hand-off summary, "equilibrado" outside the quality list, a summary "prepared" without the tool. Each was fixed, measured for false positives on the stored answers (0 each) and redeployed.
- The clean clone found two README traps: the ZIP's "é" is stored decomposed, so a typed path fails (now a glob), and the mutation net without the snapshot reported 18/78 silently (ERRORS class 1; now `NOT RUN`).
- Six catalog descriptions name another brand than their product (source-findings A12).

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
