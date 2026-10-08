"""Static security pass over the repo (Tier 0, stdlib only). Exit status 1 if anything is found.

    python3 scripts/security_check.py            # offline checks
    python3 scripts/security_check.py --online   # also fetch each CDN script and verify its integrity hash

Checks, each a function returning a list of findings:
  secrets    tracked files hold no credential-shaped strings (API keys, tokens, private keys)
  workflows  GitHub Actions: top-level permissions, actions pinned to a commit SHA, no
             pull_request_target, no ${{ github.event.* }} or head_ref pasted into a run: script
  pages      prototype/*.html: third-party scripts only from allowed CDNs and with Subresource
             Integrity, target=_blank links carry rel=noopener, no eval/new Function/document.write
  scripts    scripts/*.py: no shell=True, eval/exec, pickle, yaml.load, disabled TLS checks or
             zip/tar extractall (path traversal)
"""
import base64
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = {
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "GitHub token": r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b",
    "Anthropic API key": r"\bsk-ant-[A-Za-z0-9_-]{20,}",
    "OpenAI-style key": r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}\b",
    "Google API key": r"\bAIza[0-9A-Za-z_-]{35}\b",
    "Slack token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    "private key": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY",
}
TEXT_SUFFIXES = {".py", ".mjs", ".js", ".html", ".md", ".json", ".yml", ".yaml", ".txt", ".sh", ".toml", ".cfg", ".css", ""}
MAX_SCAN = 5_000_000          # larger tracked files are generated data (grids, embedded GeoJSON)

ALLOWED_SCRIPT_HOSTS = {"cdnjs.cloudflare.com", "cdn.jsdelivr.net"}
ALLOWED_STYLE_HOSTS = {"fonts.googleapis.com"}

# ${{ }} expressions an attacker can fill (issue/PR/comment text, branch names); they are only safe
# when passed through env: and quoted, never pasted into a shell script.
UNTRUSTED_EXPR = re.compile(r"\$\{\{[^}]*\b(github\.event\.|github\.head_ref|inputs\.)[^}]*\}\}")


def tracked_files(root=ROOT):
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
        return [root / p for p in out.decode().split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def check_secrets(files):
    found = []
    pats = {k: re.compile(v) for k, v in SECRET_PATTERNS.items()}
    for f in files:
        if f.suffix not in TEXT_SUFFIXES or not f.is_file() or f.stat().st_size > MAX_SCAN:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for name, pat in pats.items():
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                found.append(f"{f.relative_to(ROOT)}:{line}: possible {name}")
    return found


def _run_blocks(text):
    """(line number, script text) for every run: step, block or inline."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        start, indent, rest = i + 1, lines[i].index("run:"), m.group(2).strip()
        if rest and rest[0] not in "|>":
            yield start, rest
            i += 1
            continue
        body, i = [], i + 1
        while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
            body.append(lines[i])
            i += 1
        yield start, "\n".join(body)


def check_workflows(root=ROOT):
    found = []
    for wf in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        name, text = wf.relative_to(root), wf.read_text(encoding="utf-8")
        if not re.search(r"^permissions:", text, re.M):
            found.append(f"{name}: no top-level permissions: (defaults to a broad GITHUB_TOKEN)")
        if re.search(r"^\s*pull_request_target\s*:", text, re.M) or re.search(r"^on:.*pull_request_target", text, re.M):
            found.append(f"{name}: pull_request_target runs with secrets on untrusted PR code")
        for n, line in enumerate(text.split("\n"), 1):
            m = re.match(r"^\s*(?:-\s+)?uses:\s*([^\s#]+)", line)
            if m and not m.group(1).startswith("./") and not re.search(r"@[0-9a-f]{40}$", m.group(1)):
                found.append(f"{name}:{n}: action not pinned to a commit SHA: {m.group(1)}")
        for n, script in _run_blocks(text):
            for m in UNTRUSTED_EXPR.finditer(script):
                found.append(f"{name}:{n}: {m.group(0)} expanded inside a run: script (pass it through env:)")
    return found


def check_pages(root=ROOT):
    found = []
    for page in sorted((root / "prototype").rglob("*.html")):
        name, html = page.relative_to(root), page.read_text(encoding="utf-8")
        for tag in re.findall(r"<script\b[^>]*\bsrc=[^>]*>", html):
            src = re.search(r'src="([^"]+)"', tag).group(1)
            host = re.match(r"https?://([^/]+)", src)
            if not host:
                continue
            if host.group(1) not in ALLOWED_SCRIPT_HOSTS:
                found.append(f"{name}: script from unlisted host {host.group(1)}")
            if not re.search(r'\bintegrity="sha(256|384|512)-[A-Za-z0-9+/=]+"', tag) or 'crossorigin="anonymous"' not in tag:
                found.append(f"{name}: third-party script without Subresource Integrity: {src}")
        for tag in re.findall(r"<link\b[^>]*rel=\"stylesheet\"[^>]*>", html):
            host = re.search(r'href="https?://([^/"]+)', tag)
            if host and host.group(1) not in ALLOWED_STYLE_HOSTS:
                found.append(f"{name}: stylesheet from unlisted host {host.group(1)}")
        for tag in re.findall(r"<a\b[^>]*target=\"_blank\"[^>]*>", html):
            if not re.search(r'rel="[^"]*noopener', tag):
                found.append(f"{name}: target=_blank link without rel=noopener: {tag[:80]}")
        for n, line in enumerate(html.split("\n"), 1):
            for pat, what in ((r"\beval\(", "eval()"), (r"\bnew Function\(", "new Function()"), (r"document\.write\(", "document.write()")):
                if re.search(pat, line):
                    found.append(f"{name}:{n}: {what}")
    return found


PY_RULES = [
    (r"shell\s*=\s*True", "subprocess with shell=True"),
    (r"(?<![\w.])(?:eval|exec)\(", "eval/exec"),
    (r"\bpickle\.loads?\(", "pickle load"),
    (r"\byaml\.load\((?![^)]*SafeLoader)", "yaml.load without SafeLoader"),
    (r"verify\s*=\s*False|_create_unverified_context|CERT_NONE", "TLS verification disabled"),
    (r"\.extractall\(", "archive extractall (path traversal); extract members by name"),
]


def check_scripts(root=ROOT):
    found = []
    for py in sorted((root / "scripts").glob("*.py")):
        if py.name.startswith("test_") or py.name == Path(__file__).name:
            continue
        for n, line in enumerate(py.read_text(encoding="utf-8").split("\n"), 1):
            code = line.split("#", 1)[0]
            for pat, what in PY_RULES:
                if re.search(pat, code):
                    found.append(f"{py.relative_to(root)}:{n}: {what}")
    return found


def sri_tags(root=ROOT):
    """(page, src, algorithm, expected digest) for every <script integrity=...>."""
    for page in sorted((root / "prototype").rglob("*.html")):
        for tag in re.findall(r"<script\b[^>]*\bintegrity=[^>]*>", page.read_text(encoding="utf-8")):
            src = re.search(r'src="([^"]+)"', tag).group(1)
            alg, digest = re.search(r'integrity="(sha\d+)-([^"]+)"', tag).groups()
            yield page.relative_to(root), src, alg, digest


def sri_matches(data, alg, digest):
    return base64.b64encode(hashlib.new(alg, data).digest()).decode() == digest


def check_sri_online(root=ROOT):
    import urllib.request
    found, seen = [], {}
    for page, src, alg, digest in sri_tags(root):
        if src not in seen:
            with urllib.request.urlopen(src, timeout=60) as r:  # src is an allow-listed https CDN URL (check_pages)
                seen[src] = r.read()
        if not sri_matches(seen[src], alg, digest):
            found.append(f"{page}: integrity hash does not match what {src} serves")
    return found


def run(root=ROOT, online=False):
    return {"secrets": check_secrets(tracked_files(root)), "workflows": check_workflows(root),
            "pages": check_pages(root), "scripts": check_scripts(root),
            **({"sri-online": check_sri_online(root)} if online else {})}


def main():
    results = run(online="--online" in sys.argv[1:])
    total = 0
    for check, found in results.items():
        print(f"{check}: {'ok' if not found else str(len(found)) + ' finding(s)'}")
        for f in found:
            print("  " + f)
        total += len(found)
    print("PASS" if not total else f"FAIL: {total} finding(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
