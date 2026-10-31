"""Evaluate policy retrieval on the labeled set in evals/policy_retrieval.jsonl.

- base and paraphrase: a hit when an expected section is among the top 3 ranked sections;
- mixed: coverage = expected sections present in the full search result (top 3 + related).
Prints a Markdown table; with --write it also saves evals/policy-retrieval.md.

Usage: .venv/bin/python scripts/eval_retrieval.py [--write]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.tools.policies import PolicyIndex  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    index = PolicyIndex.load(ROOT / "data" / "build" / "policy_sections.json")
    cases = [json.loads(l) for l in (ROOT / "evals" / "policy_retrieval.jsonl").read_text().splitlines() if l]
    rows, totals = [], {"base": [0, 0], "paraphrase": [0, 0], "mixed": [0, 0]}
    for c in cases:
        ranked = [sid for _, sid in index.scores(c["question"])[:3]]
        returned = [r["section_id"] for r in index.search(c["question"])]
        if c["split"] == "mixed":
            got = sum(s in returned for s in c["expected_all"])
            totals["mixed"][0] += got
            totals["mixed"][1] += len(c["expected_all"])
            verdict = f"{got}/{len(c['expected_all'])}"
            expected = " + ".join(c["expected_all"])
        else:
            hit = any(s in ranked for s in c["expected_any"])
            totals[c["split"]][0] += hit
            totals[c["split"]][1] += 1
            verdict = "hit" if hit else "MISS"
            expected = " or ".join(c["expected_any"])
        rows.append(f"| {c['id']} | {c['split']} | {expected} | {', '.join(ranked)} | {', '.join(returned)} | {verdict} |")
    summary = (f"base top-3: {totals['base'][0]}/{totals['base'][1]} · "
               f"paraphrase top-3: {totals['paraphrase'][0]}/{totals['paraphrase'][1]} · "
               f"mixed coverage: {totals['mixed'][0]}/{totals['mixed'][1]} sections")
    table = "\n".join(["| Case | Split | Expected | Top 3 ranked | Returned (with related) | Result |",
                       "| --- | --- | --- | --- | --- | --- |", *rows])
    print(summary)
    print(table)
    if args.write:
        doc = f"""# Policy retrieval evaluation

Lexical BM25 over the manual's {len(index.sections)} sections (manual v{index.manual_version}), measured on
{date.today().isoformat()} with [`scripts/eval_retrieval.py`](../scripts/eval_retrieval.py) on
[`policy_retrieval.jsonl`](policy_retrieval.jsonl). The paraphrases were written after the synonym list and
were not used to tune it. This measures retrieval only; answer quality is reviewed on real conversations.

**Result:** {summary}.

{table}
"""
        (ROOT / "evals" / "policy-retrieval.md").write_text(doc)
    return 0 if totals["base"][0] >= 10 else 1


if __name__ == "__main__":
    sys.exit(main())
