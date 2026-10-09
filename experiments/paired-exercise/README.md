# Synthetic paired exercise

This is a one-task, one-replicate demonstration of the receipt checker. Both fresh `gpt-6-luna` workers received byte-identical `task.md`, starter code, and tests. The short condition received `short/context.md`; the expanded condition received `expanded/context.md`. The model and executor were held constant. Each worker could edit only its condition's implementation and evidence file.

The manifest task hash is SHA-256 of the exact UTF-8 bytes of either identical `task.md`. Each run's context hash is SHA-256 of the exact UTF-8 bytes of its condition's `context.md`. Raw run receipts are in `examples/paired-experiment-runs.json`; inputs and per-run command output are kept beside each condition.

This tiny synthetic exercise demonstrates receipt validation only. One task and one replicate do not support an inference about context quality, generalization, causality, or benchmark performance. Worker usage counters were unavailable, so no token or cost comparison is reported.
