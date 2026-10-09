# Short condition evidence

- Implementation: `count_labels(rows)` trims string labels, ignores missing/non-string/blank values, preserves case, and returns a dictionary with lexicographically sorted keys.
- Command (run from this condition directory): `python -m unittest discover -s tests -v`
- Result: PASS — 1 test ran and passed; command exited with code 0.
- Actual model: `gpt-6-luna`
- Harness: Codex subagent executor
- Usage estimate: none
