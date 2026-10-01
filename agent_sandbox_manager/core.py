"""Pure restricted interpreter. No host execution, I/O, clocks or networking."""

MAX_OPERATIONS = 100
MAX_BYTES = 65536
MAX_TEXT = 100000

class InputError(ValueError):
    """Named input validation failure."""


def fail(field, message):
    raise InputError(f"SchemaError: {field}: {message}")


def validate(record):
    if not isinstance(record, dict):
        fail("record", "must be an object")
    required = {"id", "synthetic", "operations"}
    if set(record) != required:
        fail("record.fields", f"expected {sorted(required)}; got {sorted(record)}")
    if not isinstance(record["id"], str) or not 1 <= len(record["id"]) <= 256:
        fail("id", "must be text of length 1..256")
    try:
        record["id"].encode("utf-8")
    except UnicodeEncodeError:
        fail("id", "must be valid Unicode")
    if type(record["synthetic"]) is not bool:
        fail("synthetic", "must be boolean")
    ops = record["operations"]
    if not isinstance(ops, list) or len(ops) > 1000:
        fail("operations", "must be a list with at most 1000 entries")
    for index, op in enumerate(ops):
        field = f"operations[{index}]"
        if not isinstance(op, dict) or "op" not in op:
            fail(field, "must be an object with op")
        if not isinstance(op["op"], str) or len(op["op"]) > 256:
            fail(field + ".op", "must be text of at most 256 characters")
        allowed = {"op", "path", "content"} if op["op"] == "write" else {"op", "path"}
        if set(op) != allowed:
            fail(field, f"expected fields {sorted(allowed)}")
        if not isinstance(op["path"], str) or len(op["path"]) > 4096:
            fail(field + ".path", "must be text of at most 4096 characters")
        if op["op"] == "write":
            value = op["content"]
            if not isinstance(value, str) or len(value) > MAX_TEXT:
                fail(field + ".content", f"must be text of at most {MAX_TEXT} characters")
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                fail(field + ".content", "must be valid Unicode")
    return record


def safe_path(path):
    # Portable relative paths only. Backslashes and drive syntax are denied.
    return bool(path) and not any(c in path for c in "\\:\x00") and not path.startswith("/") and all(
        part not in ("", ".", "..") for part in path.split("/")
    ) and not any(ord(c) < 32 for c in path)


def execute(record):
    validate(record)
    fs = {}
    reason = None
    completed = 0
    for op in record["operations"]:
        if completed >= MAX_OPERATIONS:
            reason = "operation_limit"
        elif op["op"] not in {"write", "read", "delete"}:
            reason = "unsupported_operation"
        elif not safe_path(op["path"]):
            reason = "unsafe_path"
        elif op["op"] in {"read", "delete"} and op["path"] not in fs:
            reason = "missing_file"
        elif op["op"] == "write":
            size = sum(len(v.encode("utf-8")) for k, v in fs.items() if k != op["path"])
            if size + len(op["content"].encode("utf-8")) > MAX_BYTES:
                reason = "byte_limit"
        if reason:
            break
        if op["op"] == "write":
            fs[op["path"]] = op["content"]
        elif op["op"] == "delete":
            del fs[op["path"]]
        completed += 1
    # Transactional rejection: no partial artifacts survive a denied job.
    if reason:
        fs = {}
    return {"id": record["id"], "synthetic": record["synthetic"],
            "status": "denied" if reason else "allowed", "reason": reason,
            "completed_operations": completed, "files": dict(sorted(fs.items())),
            "output_bytes": sum(len(v.encode("utf-8")) for v in fs.values())}


def workflow(records):
    seen = set()
    results = []
    for record in records:
        validate(record)
        if record["id"] in seen:
            fail("id", f"duplicate id {record['id']!r}")
        seen.add(record["id"])
        results.append(execute(record))
    results.sort(key=lambda r: r["id"])
    reasons = {}
    for result in results:
        if result["reason"]:
            reasons[result["reason"]] = reasons.get(result["reason"], 0) + 1
    return {"schema_version": 1, "results": results,
            "summary": {"records": len(results),
                "allowed": sum(r["status"] == "allowed" for r in results),
                "denied": sum(r["status"] == "denied" for r in results),
                "output_bytes": sum(r["output_bytes"] for r in results),
                "synthetic_records": sum(r["synthetic"] for r in results),
                "real_records": sum(not r["synthetic"] for r in results),
                "denial_reasons": dict(sorted(reasons.items()))}}
