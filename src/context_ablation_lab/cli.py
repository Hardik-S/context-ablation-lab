"""Command-line interface for local paired context-ablation analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .engine import InputError, analyze


def _reject_constant(value: str) -> None:
    raise InputError(f"non-standard JSON constant is not permitted: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _read_json(path: str) -> Any:
    """Read one UTF-8 JSON document from a user-supplied local path."""
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            return json.load(
                stream,
                parse_constant=_reject_constant,
                object_pairs_hook=_unique_object,
            )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read valid JSON from {path}: {exc}") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="context-ablate")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze_parser = commands.add_parser("analyze", help="analyze paired run records")
    analyze_parser.add_argument("manifest", help="local manifest JSON file")
    analyze_parser.add_argument("runs", help="local runs JSON file")
    analyze_parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def _text_report(report: dict[str, Any]) -> str:
    paired = report["paired"]
    lines = [f"Paired runs: {paired['count']}"]
    for condition in ("short", "expanded"):
        stats = report["conditions"][condition]
        rate = "n/a" if stats["pass_rate"] is None else f"{stats['pass_rate']:.1%}"
        lines.append(
            f"{condition}: {stats['passed']}/{stats['count']} passed ({rate}); "
            f"{stats['failed']} failed"
        )
    lines.extend(
        (
            "Discordant outcomes:",
            f"  short only passed: {paired['short_only_pass']}",
            f"  expanded only passed: {paired['expanded_only_pass']}",
        )
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the local analyzer; return 2 for invalid or incomparable inputs."""
    args = _parser().parse_args(argv)
    try:
        report = analyze(_read_json(args.manifest), _read_json(args.runs))
    except InputError as exc:
        print(f"context-ablate: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    else:
        print(_text_report(report))
    return 0
