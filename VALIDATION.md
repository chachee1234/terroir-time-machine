# Specification validation

Executed 2026-09-12 using Python `jsonschema.Draft202012Validator` with format checking. Command: `python3 /workspace/scratch/a0fc5a4c1f97/validate_spec.py`; exit code 0. The script is scratch QA tooling, not application implementation.

- PASS: Draft 2020-12 schema self-validation
- PASS: empty authoring manifest
- PASS: minimal gap fixture
- PASS: unknown field rejected
- PASS: missing visible label rejected
- PASS: age above 1000 rejected
- PASS: negative age rejected
- PASS: global ancient local anchor rejected
- PASS: geometry in gap rejected
- PASS: ancient measured scene rejected
- PASS: reconstruction without model rejected
- PASS: required file inventory

Manual document review: no app scaffold, repository, CI or deployment created; cost and scientific review boundaries are explicit. M1–M6 remain NOT RUN. Cross-record semantic checks, scientific content verification, performance and browser gates are planned, not implemented or passed. The gap fixture was generated only in memory and is not a production scene.

Environment note: the first validation attempts could not import jsonschema. Installed that validation dependency, then reran successfully. No application dependencies were installed.
