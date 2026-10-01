"""Local file CLI with atomic result and report writes."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import InputError, workflow
from .fixtures import generate
from .report import render


def load_records(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}: use asm fixtures --out demo")
    result = []
    unsupported = [p for p in directory.iterdir() if p.suffix in {".yaml", ".yml", ".csv"}]
    if unsupported:
        raise InputError(f"SchemaError: {unsupported[0]}: line 1: use JSON or JSONL input")
    # Expectations are sidecar metadata, never used to compute results.
    for path in sorted(directory.iterdir()):
        if path.name == "expectations.json" or path.suffix not in {".json", ".jsonl"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise InputError(f"ReadError: {path}: line 1: {exc}") from exc
        if path.suffix == ".jsonl":
            for line_no, line in enumerate(content.splitlines(), 1):
                if not line.strip() or line.startswith("#"):
                    continue
                try:
                    record = json.loads(line)
                    from .core import validate
                    validate(record)
                except (json.JSONDecodeError, InputError) as exc:
                    raise InputError(f"InputError: {path}: line {line_no}: {exc}") from exc
                result.append(record)
        else:
            try:
                value = json.loads(content)
                if not isinstance(value, list):
                    raise InputError("SchemaError: root: expected array of records")
                from .core import validate
                for record in value:
                    validate(record)
                result.extend(value)
            except (json.JSONDecodeError, InputError) as exc:
                raise InputError(f"InputError: {path}: line {getattr(exc, 'lineno', 1)}: {exc}") from exc
    return result


def atomic_write(path, text):
    path = Path(path)
    temp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, delete=False) as stream:
            temp = stream.name
            stream.write(text)
        os.replace(temp, path)
    except OSError as exc:
        raise InputError(f"WriteError: {path}: {exc}") from exc
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Restricted local declarative sandboxes. No arbitrary code execution.")
    sub = parser.add_subparsers(dest="command", required=True)
    fixture = sub.add_parser("fixtures", help="Generate 200 labelled synthetic jobs", epilog="Example: asm fixtures --out demo")
    fixture.add_argument("--out", required=True)
    for name, help_text in (("run", "Execute jobs in fresh virtual filesystems"),
                             ("validate", "Validate schema and identify policy denials"),
                             ("inspect", "Inspect one job and its computed virtual artifacts")):
        cmd = sub.add_parser(name, help=help_text, epilog=f"Example: asm {name} --input demo" + (" --id job-000" if name == "inspect" else ""))
        cmd.add_argument("--input", required=True)
        if name == "run":
            cmd.add_argument("--state", default=".asm/results.json")
        if name == "inspect":
            cmd.add_argument("--id", required=True)
    report = sub.add_parser("report", help="Render computed results with provenance", epilog="Example: asm report --format md")
    report.add_argument("--format", choices=["md", "json"], default="md")
    report.add_argument("--state", default=".asm/results.json")
    report.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 SYNTHETIC records; no real-world benefit measured.")
        elif args.command in {"run", "validate", "inspect"}:
            data = workflow(load_records(args.input))
            if args.command == "run":
                atomic_write(args.state, json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
                print(render(data, "json"), end="")
            elif args.command == "validate":
                print(render(data, "json"), end="")
            else:
                selected = [r for r in data["results"] if r["id"] == args.id]
                if not selected:
                    raise InputError(f"MissingJob: id {args.id!r}")
                print(json.dumps({"result": selected[0], "provenance": "synthetic" if selected[0]["synthetic"] else "author-declared real"}, ensure_ascii=True, sort_keys=True, indent=2))
        else:
            path = Path(args.state)
            if not path.is_file():
                raise InputError(f"MissingResults: {path}: run asm run --input <dir> first")
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data["schema_version"] != 1 or not isinstance(data["results"], list):
                    raise ValueError("unsupported result schema")
                output = render(data, args.format)
            except (ValueError, KeyError, TypeError) as exc:
                raise InputError(f"ResultSchemaError: {path}: line {getattr(exc, 'lineno', 1)}: {exc}") from exc
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        return 0
    except (InputError, OSError, UnicodeError) as exc:
        print(str(exc).replace(chr(0x2014), "\\u2014"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
