# Context Ablation Lab

Context Ablation Lab checks whether paired coding-agent runs differ only in the repository context supplied to the agent, then summarizes the observed pass/fail outcomes descriptively.

    python -m pip install -e ".[dev]"
    context-ablate analyze examples/manifest.json examples/runs.json

The checker validates task, model, harness and replication pairing before reporting counts. It does not call a model, judge output with an LLM, estimate cost, or claim statistical significance. Included data is synthetic; use private local files for your own experiments.

Prior work already studies context-file effects at much larger scale. This project makes no novelty, benchmark superiority, or generalization claim; it is a small local receipt-checking utility for paired experiments.
