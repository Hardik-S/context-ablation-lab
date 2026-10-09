# Context Ablation Lab

Context Ablation Lab is an offline checker for paired short-versus-expanded coding-agent context receipts. It verifies that each task and replicate has both conditions, task hashes match, model and harness are paired, and context hashes differ. It then reports deterministic pass counts, rates, and paired outcomes.

```powershell
python -m pip install -e ".[dev]"
context-ablate analyze examples/manifest.json examples/runs.json --format text
```

The included four-pair example and one-pair context exercise use synthetic data. The exercise produced one both-pass pair. It demonstrates receipt checking only; it does not establish that either context condition is better or generalizes to other tasks. No token or cost comparison is available.

The CLI makes no model or network calls and executes no submitted code. Run records are local JSON receipts; do not put private or sensitive data into public examples.
