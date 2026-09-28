#!/usr/bin/env python3
"""Copy SCENES.json "chapters" and data/plates/stylized.json into the viewer's built-in fallback copies.

prototype/timemachine.html loads both files at startup and falls back to the copies between the
/*CHAPTERS*/ ... /*END_CHAPTERS*/ and /*PLATES*/ ... /*END_PLATES*/ markers. Run this after editing
either file; scripts/test_validate.py fails while they differ. Tier 0, stdlib only.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWER = ROOT / "prototype" / "timemachine.html"


def sync(html, chapters, plates):
    ch = "[\n" + ",\n".join(" " + json.dumps(c, ensure_ascii=False) for c in chapters) + "\n]"
    pl = json.dumps(plates, separators=(",", ":"), ensure_ascii=False)
    html, n1 = re.subn(r"/\*CHAPTERS\*/.*?/\*END_CHAPTERS\*/", lambda m: f"/*CHAPTERS*/{ch}/*END_CHAPTERS*/", html, flags=re.S)
    html, n2 = re.subn(r"/\*PLATES\*/.*?/\*END_PLATES\*/", lambda m: f"/*PLATES*/{pl}/*END_PLATES*/", html, flags=re.S)
    if (n1, n2) != (1, 1):
        raise SystemExit("markers not found exactly once in the viewer")
    return html


def main():
    chapters = json.loads((ROOT / "SCENES.json").read_text())["chapters"]
    plates = json.loads((ROOT / "data" / "plates" / "stylized.json").read_text())
    old = VIEWER.read_text()
    new = sync(old, chapters, plates)
    VIEWER.write_text(new)
    print("updated" if new != old else "already in sync", VIEWER.relative_to(ROOT))


if __name__ == "__main__":
    main()
