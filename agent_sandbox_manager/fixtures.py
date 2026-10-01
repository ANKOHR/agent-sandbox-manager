"""Synthetic fixtures, deterministic construction without randomness."""
import json
from pathlib import Path


def records():
    result = []
    for i in range(200):
        if i < 120:
            ops = [{"op": "write", "path": "result.txt", "content": "ok"},
                   {"op": "read", "path": "result.txt"}]
        elif i < 140:
            ops = [{"op": "write", "path": "../escape", "content": "x"}]
        elif i < 160:
            ops = [{"op": "exec", "path": "command"}]
        elif i < 175:
            ops = [{"op": "write", "path": "large", "content": "x" * 65537}]
        elif i < 190:
            ops = [{"op": "write", "path": "a", "content": "x"}] * 101
        else:
            ops = [{"op": "read", "path": "absent"}]
        result.append({"id": f"job-{i:03d}", "synthetic": True, "operations": ops})
    return result


def expectations():
    # Hand computed from index ranges, independent of the engine:
    # 120 successes * 2 UTF-8 bytes = 240 output bytes; 80 denials.
    return {"synthetic": True, "summary": {"records": 200, "allowed": 120,
        "denied": 80, "output_bytes": 240, "synthetic_records": 200,
        "real_records": 0, "denial_reasons": {"unsafe_path": 20,
        "unsupported_operation": 20, "byte_limit": 15, "operation_limit": 15,
        "missing_file": 10}},
        "denied_ids": [f"job-{i:03d}" for i in range(120, 200)]}


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "jobs.jsonl").write_text("# SYNTHETIC fixture data, no real trials\n" +
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records()), encoding="utf-8")
    (out / "expectations.json").write_text(json.dumps(expectations(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "LABEL.md").write_text("<!-- SYNTHETIC -->\nAll fixture records are synthetic. No measured real-world benefit.\n", encoding="utf-8")
