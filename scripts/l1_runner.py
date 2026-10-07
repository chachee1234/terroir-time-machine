"""Workflow H: draft the ready L1 task cards in queue/cards/ with FreeLLMAPI.

GOVERNANCE.md §2a and queue/README.md. Standard library plus jsonschema (requirements.txt).
The model only returns text; this script decides what it reads and where the draft goes,
runs the mechanical checks, and updates each card's status. It never commits; the
workflow's L0 steps do. Drafts are untrusted until Claude checks them.

  python3 scripts/l1_runner.py --pending          # print how many L1 cards are ready
  python3 scripts/l1_runner.py --dry-run          # show what would be sent, call nothing
  FREELLMAPI_KEY=... python3 scripts/l1_runner.py --base-url http://127.0.0.1:3001
"""

import argparse
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

import jsonschema

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS_DIR = os.path.join("queue", "cards")
CARD_SCHEMA = os.path.join("queue", "card.schema.json")
DRAFTS_DIR = "data/drafts/l1/"
SWITCH_ON = "**Switch:** `FreeLLMAPI: ON`"
MAX_INPUT_CHARS = 60000
MAX_ATTEMPTS = 3
DENIED_PREFIXES = ("data/raw/", "uploads/", "data/drafts/")
DENIED_SUFFIXES = (".env", ".pem", ".key", ".p12", ".pfx")

SYSTEM_PROMPT = (
    "You draft text for an open-source geology and wine-region map. Use only the facts in the "
    "input files. Do not add facts, ages, numbers, names or sources that are not in them; when "
    "something is missing, write GAP instead. Follow the task exactly and return only the "
    "requested output, with no preamble."
)


def load_cards(root):
    schema = json.load(open(os.path.join(root, CARD_SCHEMA), encoding="utf-8"))
    cards = []
    for path in sorted(glob.glob(os.path.join(root, CARDS_DIR, "*.json"))):
        with open(path, encoding="utf-8") as fh:
            card = json.load(fh)
        jsonschema.validate(card, schema)
        if card["id"] != os.path.splitext(os.path.basename(path))[0]:
            raise ValueError(f"{path}: id '{card['id']}' does not match the file name")
        cards.append((path, card))
    return cards


def ready_l1(cards):
    return [(p, c) for p, c in cards if c["layer"] == "L1" and c["status"] == "ready"]


def switch_on(root):
    path = os.path.join(root, "GOVERNANCE.md")
    return os.path.exists(path) and SWITCH_ON in open(path, encoding="utf-8").read()


def safe_input(root, rel):
    """Return the absolute path of an allowed input, or raise ValueError."""
    norm = os.path.normpath(rel).replace(os.sep, "/")
    if os.path.isabs(rel) or norm.startswith("../") or norm == "..":
        raise ValueError(f"input outside the repository: {rel}")
    if any(part.startswith(".") for part in norm.split("/")):
        raise ValueError(f"hidden file not allowed: {rel}")
    if norm.startswith(DENIED_PREFIXES) or norm.lower().endswith(DENIED_SUFFIXES):
        raise ValueError(f"input not allowed for L1: {rel}")
    full = os.path.realpath(os.path.join(root, norm))
    if not full.startswith(os.path.realpath(root) + os.sep):
        raise ValueError(f"input outside the repository: {rel}")
    if not os.path.isfile(full):
        raise ValueError(f"input not found: {rel}")
    return full


def check_paths(root, card):
    out = os.path.normpath(card["output"]).replace(os.sep, "/")
    if not out.startswith(DRAFTS_DIR):
        raise ValueError(f"output must be under {DRAFTS_DIR}: {card['output']}")
    if card.get("output_schema"):
        safe_input(root, card["output_schema"])


def build_prompt(root, card):
    check_paths(root, card)
    parts, total = [], 0
    for rel in card["inputs"]:
        text = open(safe_input(root, rel), encoding="utf-8").read()
        total += len(text)
        if total > MAX_INPUT_CHARS:
            raise ValueError(f"inputs exceed {MAX_INPUT_CHARS} characters")
        parts.append(f"=== {rel} ===\n{text}")
    fmt = "a single JSON value" if card["format"] == "json" else "Markdown"
    limit = f" Keep it under {card['max_chars']} characters." if card.get("max_chars") else ""
    user = f"Task: {card['task']}\nReturn {fmt}.{limit}\n\nInput files:\n\n" + "\n\n".join(parts)
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def call_model(base_url, key, messages, timeout=180):
    body = json.dumps({"model": "auto", "messages": messages, "temperature": 0.2}).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"] or "", data.get("model", "unknown")


def strip_fences(text):
    match = re.fullmatch(r"\s*```[a-zA-Z]*\n(.*?)\n?```\s*", text, re.S)
    return match.group(1) if match else text.strip()


def check_draft(root, card, text):
    """Return (content to write, problem or None)."""
    text = strip_fences(text)
    if not text:
        return text, "empty answer"
    if card.get("max_chars") and len(text) > card["max_chars"]:
        return text, f"draft is {len(text)} characters, over max_chars {card['max_chars']}"
    if card["format"] == "json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError as err:
            return text, f"not valid JSON: {err}"
        if card.get("output_schema"):
            schema = json.load(open(safe_input(root, card["output_schema"]), encoding="utf-8"))
            try:
                jsonschema.validate(value, schema)
            except jsonschema.ValidationError as err:
                return text, f"fails {card['output_schema']}: {err.message}"
        text = json.dumps(value, indent=2, ensure_ascii=False)
    return text + "\n", None


def save_card(path, card):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(card, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def write_draft(root, card, content, model):
    out = os.path.join(root, card["output"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(content)
    meta = {"card": card["id"], "drafted_by": f"FreeLLMAPI ({model})", "untrusted": True,
            "checked_by_claude": False}
    with open(out + ".meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
        fh.write("\n")


def run(root, base_url, key, limit, dry_run=False, call=call_model):
    """Draft up to `limit` ready L1 cards. Returns a list of (card id, new status, note)."""
    results = []
    for path, card in ready_l1(load_cards(root))[:limit]:
        try:
            messages = build_prompt(root, card)
        except (ValueError, UnicodeDecodeError) as err:
            card.update(status="blocked", note=str(err))
            results.append((card["id"], "blocked", str(err)))
            if not dry_run:
                save_card(path, card)
            continue
        if dry_run:
            results.append((card["id"], "would-draft", f"{len(messages[1]['content'])} characters"))
            continue
        card["attempts"] = card.get("attempts", 0) + 1
        try:
            text, model = call(base_url, key, messages)
        except (urllib.error.URLError, OSError, KeyError, IndexError, ValueError) as err:
            note = f"model call failed: {err}"
            if card["attempts"] >= MAX_ATTEMPTS:
                card.update(status="blocked", note=note)
            else:
                card["note"] = note
            save_card(path, card)
            results.append((card["id"], card["status"], note))
            continue
        content, problem = check_draft(root, card, text)
        write_draft(root, card, content, model)
        if problem:
            card.update(status="failed-check", note=problem)
        else:
            card.update(status="drafted", note=f"drafted by FreeLLMAPI ({model}); waiting for Claude's check")
        save_card(path, card)
        results.append((card["id"], card["status"], card["note"]))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--base-url", default="http://127.0.0.1:3001")
    ap.add_argument("--limit", type=int, default=5, help="cards per run (default 5)")
    ap.add_argument("--pending", action="store_true", help="print the number of ready L1 cards")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if args.pending:
        print(len(ready_l1(load_cards(args.root))))
        return 0
    if not switch_on(args.root):
        print("GOVERNANCE.md switch is FreeLLMAPI: OFF; nothing sent.")
        return 0
    key = os.environ.get("FREELLMAPI_KEY", "")
    if not key and not args.dry_run:
        print("FREELLMAPI_KEY is not set.", file=sys.stderr)
        return 2
    for card_id, status, note in run(args.root, args.base_url, key, args.limit, args.dry_run):
        print(f"{card_id}: {status} ({note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
