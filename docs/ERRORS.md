# Error catalog

> Errors that **the agent** actually made in this project, organized by class. When a defect shows up, open this file before fixing it and ask: *which class here is this an instance of?*

## Index

| # | Class | Occurrences | One-line antidote |
| --- | --- | --- | --- |
| 1 | A test passed for a reason other than the rule it claimed to protect | 3 | Run the mutation that removes the rule; the named test must fail |
| 2 | Recommended a date without doing the calendar math | 1 | Before proposing a deadline, compute the weekday and the business-day rule from the source text |

---

### 1. A test passed for a reason other than the rule it claimed to protect

**2026-10-31 — `to_cents` with float.** Replacing `Decimal` with `float` in `to_cents` left every test green. The chosen values (599.9, 0.1) happen to survive float rounding. The mutation net caught it; the test now includes 0.29 and 1.15, which fail in float.

**2026-10-31 — function allowlist.** Replacing the SQLite function allowlist with "allow all" left the violation test green. The only function case was `load_extension`, which Python already blocks on its own. Added `randomblob` and `sqlite_version`, which exist and are not on the list.

**2026-10-31 — row cap.** `test_rows_read_are_capped_without_limit` asserted `<= 65` on a cross join, but deduplication already guarantees at most 65 IDs, so removing the cap could never fail it. Found during the second review pass; the test now lowers the cap to 5 and expects exactly 5 IDs.

> **A green test proves only what a mutation of the rule can make it fail.**

**The antidote:** every new rule gets an entry in `scripts/mutation_check.py`, and the named test must fail.

### 2. Recommended a date without doing the calendar math

**2026-10-31 — deadline.** In the first planning round I offered "02/11" as the recommended deadline without computing that 2026-10-31 is a Saturday or reading the business-day rule. When Breno shared the selection e-mail, the rule ("today + two business days") gave Tue 2026-11-03 (or Wed 2026-11-04 if Nov 2 is not counted). The earlier plan was one day tighter than necessary.

> **A deadline is a calculation from a source text, not an option to pick.**

**The antidote:** quote the source sentence and run `date` or `python -c` for the weekday before proposing any deadline.
