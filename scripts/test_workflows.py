"""Checks the Claude steps in .github/workflows.

Structured output is returned through Claude Code's built-in `StructuredOutput`
tool. A step that passes --json-schema together with an --allowedTools list that
omits StructuredOutput finishes without structured_output (seen in intake runs
36106437203 and 36107308738). Runs under pytest or `python3 scripts/test_workflows.py`.
"""

import glob
import json
import os
import re
import shlex
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE_ARGS = re.compile(r"claude_args: >-\n((?:\s{12}.*\n?)+)")


def claude_steps():
    """Yield (workflow file, parsed claude_args tokens) for each Claude step."""
    for path in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        with open(path, encoding="utf-8") as fh:
            for match in CLAUDE_ARGS.finditer(fh.read()):
                folded = " ".join(line.strip() for line in match.group(1).splitlines())
                yield os.path.basename(path), shlex.split(folded)


def flag(tokens, name):
    return tokens[tokens.index(name) + 1] if name in tokens else None


class ClaudeSteps(unittest.TestCase):
    def test_steps_found(self):
        self.assertEqual(sorted(name for name, _ in claude_steps()), ["region-intake.yml", "sunday-audit.yml"])

    def test_structured_output_tool_allowed(self):
        for name, tokens in claude_steps():
            with self.subTest(workflow=name):
                self.assertIsNotNone(flag(tokens, "--json-schema"))
                self.assertIn("StructuredOutput", flag(tokens, "--allowedTools").split(","))

    def test_schemas_are_json(self):
        for name, tokens in claude_steps():
            with self.subTest(workflow=name):
                self.assertEqual(json.loads(flag(tokens, "--json-schema"))["type"], "object")

    def test_models_match_governance(self):
        models = {name: flag(tokens, "--model") for name, tokens in claude_steps()}
        self.assertEqual(models, {"region-intake.yml": "claude-haiku-4-5-20251001",
                                  "sunday-audit.yml": "claude-opus-5-5"})

    def test_no_write_or_shell_tools(self):
        for name, tokens in claude_steps():
            with self.subTest(workflow=name):
                allowed = set(flag(tokens, "--allowedTools").split(","))
                self.assertEqual(allowed & {"Bash", "Edit", "Write", "WebFetch", "WebSearch"}, set())


if __name__ == "__main__":
    unittest.main()
