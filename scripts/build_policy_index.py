"""Build the store-manual index by section, for policy retrieval.

Reads the manual PDF with pypdf (layout mode), splits it at numbered headings that start a line, keeps the pages
of each section, turns table rows into "a | b | c" lines and adds explicit links between sections whose rules
must be read together. The expected section list is fixed: a missing or extra heading stops the build, so a
new manual version cannot silently produce a different index.

Writes `data/build/policy_sections.json` (ignored by Git, see D15). The section texts are not versioned in the
public repository because the manual is an internal document.

Usage: .venv/bin/python scripts/build_policy_index.py [--source <challenge ZIP | directory | manual.pdf>]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "_private_inputs" / "challenge"
DEFAULT_OUT = ROOT / "data" / "build" / "policy_sections.json"
MANUAL_SUFFIX = "data/políticas_da_loja.pdf"

EXPECTED_IDS = ["1", "1.1", "1.2", "2", "3", "3.1", "4", "4.1", "4.2", "4.3", "4.4", "5", "5.1", "5.2", "5.3",
                "6", "6.1", "6.2", "7", "7.1", "7.2", "7.3", "8", "8.1", "8.2", "8.3", "9", "10"]

# Rules that only make sense together (guide 02 §6). Retrieval adds these when one side is found.
RELATED = {
    "3": ["3.1", "6.2"], "3.1": ["3"], "6.2": ["3"], "6.1": ["6.2"],
    "4.1": ["4"], "4.2": ["8.1", "8.3"], "4.3": ["4.4"], "4.4": ["4.3"], "8.1": ["4.2"], "8.2": ["8.1"],
    "8.3": ["8.1"], "5.1": ["5"], "5.2": ["5.3"], "5.3": ["5.2"], "7.3": ["7.1"], "2": ["7.1"], "1.2": ["7"],
}

HEADING_RE = re.compile(r"^(\d{1,2}(?:\.\d)?)\.?\s+(\S.*)$")
NOISE_RE = re.compile(r"^(Empório da Música\s+Manual de Políticas e Procedimentos|Página\s+\d+)$")


def read_manual(source: Path) -> bytes:
    """Manual bytes from the challenge ZIP, a directory that contains it, or the PDF itself."""
    nfc = lambda name: unicodedata.normalize("NFC", name)  # noqa: E731 - names arrive in NFD
    if source.is_file() and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as z:
            members = [m for m in z.namelist() if nfc(m).endswith(MANUAL_SUFFIX)]
            if len(members) == 1:
                return z.read(members[0])
    elif source.is_dir():
        members = [p for p in source.rglob("*.pdf") if nfc(p.as_posix()).endswith(MANUAL_SUFFIX)]
        if len(members) == 1:
            return members[0].read_bytes()
    elif source.suffix.lower() == ".pdf" and source.is_file():
        return source.read_bytes()
    raise SystemExit(f"ERROR: expected exactly one '{MANUAL_SUFFIX}' in {source}")


def clean_line(line: str) -> str:
    line = line.replace("​", "").rstrip()
    if re.match(r"^\s{0,2}\S", line) and re.search(r"\S\s{3,}\S", line):
        return " | ".join(part.strip() for part in re.split(r"\s{3,}", line.strip()))  # table row
    return " ".join(line.split())


def join_wrapped(lines: list[str]) -> list[str]:
    """Re-join sentences that the PDF wrapped; bullets, table rows and lines after ':' or '.' start anew."""
    out: list[str] = []
    for line in lines:
        starts_new = line.startswith("•") or " | " in line or re.match(r"^\d+\.\s", line)
        if out and not starts_new and " | " not in out[-1] and not out[-1].endswith((".", ":")):
            out[-1] = f"{out[-1]} {line}"
        else:
            out.append(line)
    return out


def split_sections(raw: bytes) -> tuple[str, list[dict]]:
    reader = PdfReader(io.BytesIO(raw))
    sections: list[dict] = []
    version = ""
    for page_no, page in enumerate(reader.pages, start=1):
        text = unicodedata.normalize("NFC", page.extract_text(extraction_mode="layout"))
        if page_no == 1:
            m = re.search(r"Versão\s+([\d.]+)", text)
            version = m.group(1) if m else ""
            continue  # cover page: title, address and contacts (also in §1.2)
        for raw_line in text.splitlines():
            if not raw_line.strip() or NOISE_RE.match(raw_line.strip()):
                continue
            heading = HEADING_RE.match(raw_line) if not raw_line[:1].isspace() else None
            if heading and heading.group(1) in EXPECTED_IDS and heading.group(1) not in {s["id"] for s in sections}:
                sections.append({"id": heading.group(1), "title": heading.group(2).strip(), "page_start": page_no,
                                 "page_end": page_no, "lines": []})
                continue
            if sections:
                sections[-1]["lines"].append(clean_line(raw_line))
                sections[-1]["page_end"] = page_no
    found = [s["id"] for s in sections]
    if found != EXPECTED_IDS:
        raise SystemExit(f"ERROR: manual sections differ from the expected list.\n  expected {EXPECTED_IDS}\n  found    {found}")
    source_hash = hashlib.sha256(raw).hexdigest()
    out = []
    for s in sections:
        body = "\n".join(join_wrapped([line for line in s["lines"]
                                       if line and not line.startswith("Empório da Música — Sua música")]))
        out.append({"id": s["id"], "title": s["title"], "page_start": s["page_start"], "page_end": s["page_end"],
                    "text": body.strip(), "related_ids": RELATED.get(s["id"], []), "source_hash": source_hash})
    return version, out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                        help="challenge ZIP, a directory containing it extracted, or the manual PDF")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    version, sections = split_sections(read_manual(args.source))
    index = {"manual_version": version, "source_hash": sections[0]["source_hash"], "sections": sections}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"manual_version": version, "sections": len(sections), "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
