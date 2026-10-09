"""azdiagram INPUT.yaml [-o OUTPUT.drawio] ..."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import DiagramError, build
from .drawio import to_drawio
from .layout import layout
from .loader import ValidationFailed, load


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="azdiagram", description=__doc__)
    parser.add_argument("input", type=Path, help="YAML file describing the infrastructure")
    parser.add_argument("-o", "--output", type=Path, help="output .drawio file (default: INPUT with .drawio suffix)")
    parser.add_argument("--no-descriptions", action="store_true", help="omit descriptions from labels")
    parser.add_argument("--direction", choices=["horizontal", "vertical"], help="arrangement of top-level sections")
    parser.add_argument("--validate-only", action="store_true", help="validate the YAML and exit")
    args = parser.parse_args(argv)

    try:
        doc = load(args.input)
        diagram = build(
            doc,
            show_descriptions=False if args.no_descriptions else None,
            direction=args.direction,
        )
    except ValidationFailed as e:
        for err in e.errors:
            print(f"{args.input}: {err}", file=sys.stderr)
        return 1
    except DiagramError as e:
        print(f"{args.input}: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"azdiagram: {e}", file=sys.stderr)
        return 2

    if args.validate_only:
        print(f"{args.input}: ok")
        return 0

    layout(diagram)
    output = args.output or args.input.with_suffix(".drawio")
    output.write_text(to_drawio(diagram), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
