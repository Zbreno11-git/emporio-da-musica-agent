# Use of AI assistants

> This is a challenge deliverable. It records only what actually happened, with dates, and is updated throughout the project. For each use, it separates what the tool did, what I (Breno) decided and how the result was verified.

## Tools

| Tool | Role |
| --- | --- |
| Claude Code (Opus) | Implementation, audit of the source material, tests and documentation, guided by process and technical skills |
| ChatGPT | Brainstorming and spec definition before implementation (vision, backend and branding guides) |
| GPT Images | Ressonância brand board and the universal catalog thumbnail (recorded in the branding guide) |

## Log by session

### 2026-10-31 · Session 0, setup (Claude Code)

- **What Claude Code did:**
  - read the case, the manual, the CSVs and the three guides;
  - recomputed the reference values from the CSVs (0 differences) and listed the manual's inconsistencies in [`source-findings.md`](source-findings.md);
  - created `.venv`, `.gitignore` and the initial documentation;
  - installed three skills pinned by commit, checking the blobs;
  - created the dedicated GCP project and the public repository.
- **What I decided:** the stack, brand, policy flow and a separate GCP project. These decisions came before this session, in the guides, and were restated in the opening prompt.
- **How I verified:** checking scripts ran on the original files; before the push I reviewed the diff and ran the secrets and personal-data scan.

### 2026-10-31 · Planning, S1 and the English switch (Claude Code)

- **What Claude Code did:**
  - ran two rounds of planning questions;
  - found that the Gemini key belongs to another GCP project and that the billing account is in BRL;
  - wrote the two-day plan;
  - implemented the importer, the pricing rules and the restricted SQL executor, test-first. It verified the tests with a curated mutation net, where two mutations initially escaped and the tests were strengthened;
  - after I shared the selection e-mail, flagged that 2026-10-31 is a Saturday, that the deadline is later than I assumed and that delivery is an English PDF via Google Forms;
  - translated the repository to English.
- **What I decided:** the deadline, the benchmark candidates, the budget, the delivery blockers, keeping the current Gemini key, the language scope (English repository, Portuguese customer-facing agent) and the delivery format.
- **How I verified:** `pytest` (62 passed), `scripts/mutation_check.py` (15/15 caught) and `scripts/check_staged.py` before each commit.

### 2026-10-31 · S2–S8: agent, deploy, benchmark, UI, QA, security and delivery (Claude Code)

- **What Claude Code did:**
  - built the Gemini tool loop, the order and manual tools, the hand-off and the server-side text checks, test-first, with a scripted fake model for every test (labeled as a mock);
  - deployed the demo to Cloud Run in the dedicated project, after my authorization, and verified each revision on the URL;
  - ran the model cost-benefit benchmark and built the measured cost model from its turns;
  - built the Ressonância interface and `/admin`, then the browser tests, the hardening and the QA report with screenshots;
  - reviewed real answers and turned each invented fact it found (a non-existent bass model, false "we don't have it", sound qualities not in the data, a fake price or discount accepted from an injected message, a false absence under attack) into a server check, each with a test and a mutation;
  - wrote and ran the red-team battery, and captured and reviewed the five delivery conversations.
- **What I decided:** the scope and the order of the sessions; the budget and every deploy; the model candidates; the `/admin` content and its privacy rule; the testing and hardening session; that invented products, numbers or hallucination must be avoided "a todo custo"; that the agent must be defended against prompt injection and other LLM attacks; the delivery format.
- **ChatGPT:** used before implementation for brainstorming and to write the vision, backend and branding specs (guides 01–03) that the implementation followed.
- **How I verified:** `pytest` (200 passed), `scripts/mutation_check.py` (78/78 mutations caught), `scripts/check_staged.py` before every commit, the hosted QA run (13/13 hosted cases passed), the red-team battery (0 blockers) and the reviewed conversations in `examples/`. Claude Code's own mistakes and their antidotes are in [`ERRORS.md`](ERRORS.md).
