# Expanded condition evidence

- Implementation: `count_labels(rows)` trims string labels, ignores missing, non-string, and whitespace-only labels, preserves case, and returns keys in lexicographic order.
- Command, run from this condition directory: `python -m unittest discover -s tests -v`
- Result: PASS; 1 test ran and passed (`OK`, exit code 0).
- Actual model: `gpt-6-luna`.
- Harness: Codex subagent executor.
- Usage estimate: none provided.
