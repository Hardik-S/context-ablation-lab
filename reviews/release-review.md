# Release review

## BLOCK — 2026-10-09

The paired-count core meets the frozen matrix/pairing contract on the supplied synthetic fixture: it checks the complete task × replicate × condition matrix, rejects duplicate run IDs and duplicate task/replicate cells, validates task hashes, model and harness agreement, and requires distinct paired context hashes. Counts and output ordering are deterministic and descriptive; the CLI contains no network, model, or code-execution path. The checked-in examples are synthetic.

The full suite passes (`20 passed`). A fresh temporary virtual environment successfully installed the documented editable package with its dev extra, passed the suite (`20 passed`), and ran both `python -m context_ablation_lab analyze ... --format json` and the installed `context-ablate ... --format text` quickstart. Setuptools emitted a deprecation warning for the TOML table form of `project.license`; it did not prevent installation.

### Release blockers

1. **Empty designs are accepted as complete.** With a valid manifest changed to `{"tasks": [], ...}` and runs document `{"version": 1, "runs": []}`, `analyze` returns success with zero counts and null pass rates. An empty `replicates` array behaves the same. This lets an incomplete/no-op experiment satisfy the complete-matrix check. Reject empty task and replicate lists.
2. **The CLI accepts non-standard or ambiguous JSON.** Python's default `json.load` accepts `NaN` and silently keeps the last duplicate object key. Reproduction: replace one fixture run's evidence with `{"score": NaN}`; `context-ablate analyze ...` still succeeds with 4 pairs. Replace its evidence field with two `evidence` keys (for example `"evidence":"first", "evidence":"second"`); it also succeeds. These are malformed/ambiguous inputs, even though the evidence is ignored. Reject non-finite JSON constants and duplicate keys during parsing; add CLI regression tests.

### Bounded fix advice

Add non-empty checks for manifest tasks and replicates. Configure JSON decoding to reject duplicate keys and `NaN`/`Infinity` constants, with a concise `InputError`/CLI diagnostic. Add tests for these three cases, then rerun the suite and quickstart.

## Independent follow-up — PASS — 2026-10-09

Reviewed the bounded repair independently. The original BLOCK and repair record above remain intact. This follow-up found the reported release blockers repaired and the targeted mismatch branches working.

### Commands and results

- `python -m pytest -q` — **24 passed in 1.94s**.
- Created a fresh virtual environment under `%TEMP%\context-ablation-release-cbe4562612c947318fca1a5bd8e26bb6` with `python -m venv <temp-venv>`, then ran `python -m pip install -e ".[dev]"` from the repository — **editable package and pytest 8.4.2 installed successfully**.
- In that clean environment, `python -m pytest -q` — **24 passed in 1.74s**.
- In that clean environment, `python -m context_ablation_lab analyze examples/manifest.json examples/runs.json --format json` — **exit 0**; 4 pairs, each condition 2/4 passed (50%), discordances 1 each.
- In that clean environment, `context-ablate analyze examples/manifest.json examples/runs.json --format text` — **exit 0**; same 4-pair summary.

### Adversarial CLI reproductions

Ran the CLI in the fresh environment against temporary copies of the synthetic fixture, changing one condition at a time. All invalid cases exited **2**, emitted no report on stdout, and returned a specific diagnostic on stderr:

- Empty manifest `tasks`: `manifest.tasks must contain at least one task`.
- Empty manifest `replicates`: `manifest.replicates must contain at least one replicate`.
- Nested `NaN` inside an evidence object/list: `non-standard JSON constant is not permitted: NaN`.
- Duplicate key nested in an evidence object: `duplicate JSON object key: x`.
- Task hash differing from the manifest: `runs.runs[1].task_sha256 does not match the manifest`.
- Paired model mismatch: `paired runs for task synthetic-task-a, replicate replicate-1 have mismatched model`.
- Paired harness mismatch: `paired runs for task synthetic-task-a, replicate replicate-1 have mismatched harness`.
- Removed expected run: `missing run for task synthetic-task-a, replicate replicate-1, condition expanded`.

The nested JSON cases confirm strict parsing applies recursively, including within otherwise ignored evidence. The checked-in examples identify tasks, runs, model, harness and evidence as synthetic. A source/example/README scan for HTTP, socket, subprocess, shell execution, `eval`, and `exec` paths found no matches; the CLI remains local receipt parsing and summarization, with no network, model call, or code execution path.

No files outside this review record were changed. No commit or push was made.

### Exact clean-environment command forms

The temporary environment path used for this pass was `C:\Users\hshre\AppData\Local\Temp\context-ablation-release-cbe4562612c947318fca1a5bd8e26bb6`. The PowerShell command forms were:

```powershell
python -m venv $reviewVenv
& $reviewPy -m pip install -e ".[dev]"
& $reviewPy -m pytest -q
& $reviewPy -m context_ablation_lab analyze examples/manifest.json examples/runs.json --format json
& "$reviewVenv\Scripts\context-ablate.exe" analyze examples/manifest.json examples/runs.json --format text
```
