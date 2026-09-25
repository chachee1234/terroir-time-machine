"""Checks the --json-schema values in .github/workflows against structured-output limits.

Structured outputs reject numeric and string-length constraints and type arrays, and
require additionalProperties: false on every object. An unsupported schema makes the
model finish without structured_output, which fails the intake and audit jobs.
Runs under pytest or `python3 scripts/test_workflows.py`.
"""

import glob
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_ARG = re.compile(r"--json-schema '(.*?)'", re.S)
UNSUPPORTED = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
               "minLength", "maxLength", "pattern"}


def workflow_schemas():
    for path in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        with open(path, encoding="utf-8") as fh:
            for match in SCHEMA_ARG.finditer(fh.read()):
                yield os.path.basename(path), json.loads(match.group(1))


def problems(node, where="$"):
    found = []
    if isinstance(node, dict):
        for key in UNSUPPORTED & node.keys():
            found.append(f"{where}: unsupported keyword '{key}'")
        if isinstance(node.get("type"), list):
            found.append(f"{where}: type array {node['type']}; use anyOf")
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            found.append(f"{where}: object without additionalProperties: false")
        for key, value in node.items():
            found.extend(problems(value, f"{where}.{key}"))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found.extend(problems(value, f"{where}[{i}]"))
    return found


class WorkflowSchemas(unittest.TestCase):
    def test_schemas_found(self):
        self.assertEqual(sorted(name for name, _ in workflow_schemas()),
                         ["region-intake.yml", "sunday-audit.yml"])

    def test_schemas_use_supported_features_only(self):
        for name, schema in workflow_schemas():
            with self.subTest(workflow=name):
                self.assertEqual(problems(schema), [])

    def test_checker_catches_old_intake_schema(self):
        old = {"type": "object", "properties": {"lat": {"type": ["number", "null"], "minimum": -90},
                                                "src": {"type": "object"}}}
        self.assertEqual(len(problems(old)), 4)


if __name__ == "__main__":
    unittest.main()
