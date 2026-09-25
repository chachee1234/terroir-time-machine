"""Summarize unittest output on stdin as 'passed/total' for the weekly digest."""

import re
import sys


def summarize(text):
    ran = re.search(r"^Ran (\d+) tests?", text, re.MULTILINE)
    if not ran:
        return "tests did not run"
    total = int(ran.group(1))
    failed = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", text))
    skipped = re.search(r"skipped=(\d+)", text)
    summary = f"{total - failed}/{total}"
    if skipped:
        summary += f" ({skipped.group(1)} skipped)"
    return summary


if __name__ == "__main__":
    print(summarize(sys.stdin.read()))
