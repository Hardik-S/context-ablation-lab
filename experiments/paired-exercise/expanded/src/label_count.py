"""Count normalized nonempty labels in synthetic CSV-like rows."""


def count_labels(rows):
    """Return label counts; implement the behavior in the paired task packet."""
    counts = {}
    for row in rows:
        label = row.get("label")
        if not isinstance(label, str):
            continue
        label = label.strip()
        if label:
            counts[label] = counts.get(label, 0) + 1
    return {label: counts[label] for label in sorted(counts)}
