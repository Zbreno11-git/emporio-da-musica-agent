"""Pre-commit scan of staged files (git add).

Fails (exit 1) if any staged file contains:
- the GEMINI_API_KEY value from the local .env, or token/private-key patterns;
- a customer name, e-mail or phone number from the original customers.csv;
- a verbatim sentence (>= 80 characters) from the store's internal manual;
- a relative Markdown link to a file that will not be in the repository.

Prints only counts and file paths, never the sensitive values.
Usage: .venv/bin/python scripts/check_staged.py
"""

import csv
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVATE_DATA = os.path.join(ROOT, "_private_inputs", "challenge", "*", "data")
TOKEN_PATTERNS = [r"AIza[0-9A-Za-z_\-]{20,}", r"gh[opsu]_[0-9A-Za-z]{20,}", r"private_key", r"-----BEGIN"]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def main():
    staged = [f for f in git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split("\0") if f]
    blobs = {f: git("show", f":{f}") for f in staged}
    tracked = set(git("ls-files", "-z").split("\0")) | set(staged)
    fails = 0

    env_path = os.path.join(ROOT, ".env")
    key = ""
    if os.path.exists(env_path):
        key = next((l.split("=", 1)[1].strip() for l in open(env_path) if l.startswith("GEMINI_API_KEY=")), "")
    hits = sum(key in b for b in blobs.values()) if key else 0
    print(f".env key value: {hits} hit(s) (key loaded: {bool(key)})")
    fails += hits

    # This file holds the patterns themselves; the real-key check above still applies to it.
    for pat in TOKEN_PATTERNS:
        found = [f for f, b in blobs.items() if f != "scripts/check_staged.py" and re.search(pat, b)]
        print(f"pattern {pat}: {len(found)} {found}")
        fails += len(found)

    customers = [p for p in glob.glob(os.path.join(PRIVATE_DATA, "*")) if p.endswith("customers.csv")]
    if customers:
        rows = list(csv.DictReader(open(customers[0], encoding="utf-8-sig")))
        pii = sum(
            1
            for r in rows
            for k in ("name", "email", "phone")
            if len(r[k].strip()) >= 6 and any(r[k].strip() in b for b in blobs.values())
        )
        print(f"customer data (name/e-mail/phone): {pii} of {len(rows) * 3} values")
        fails += pii
    else:
        print("WARNING: customers.csv not found; personal-data check did not run")
        fails += 1

    manuals = glob.glob(os.path.join(PRIVATE_DATA, "*.pdf"))
    if manuals:
        text = subprocess.run(["pdftotext", manuals[0], "-"], capture_output=True, text=True).stdout
        sentences = [s.strip() for s in re.split(r"(?<=[.:;])\s+", " ".join(text.split())) if len(s.strip()) >= 80]
        public = " ".join(" ".join(b.split()) for b in blobs.values())
        copied = [s[:50] for s in sentences if s in public]
        print(f"verbatim manual sentences (of {len(sentences)} compared): {len(copied)} {copied}")
        fails += len(copied)
    else:
        print("WARNING: manual not found; verbatim-copy check did not run")
        fails += 1

    broken = []
    for f, b in blobs.items():
        if not f.endswith(".md"):
            continue
        for target in re.findall(r"\]\(([^)\s]+)\)", b):
            path = target.split("#")[0]
            if not path or re.match(r"[a-z]+:", path):
                continue
            norm = os.path.normpath(os.path.join(os.path.dirname(f), path))
            if norm not in tracked and not any(t.startswith(norm + "/") for t in tracked):
                broken.append((f, target))
    print(f"broken relative links: {broken}")
    fails += len(broken)

    print("RESULT:", "PASS" if fails == 0 else f"FAIL ({fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
