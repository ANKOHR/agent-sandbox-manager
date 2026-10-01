# Agent Sandbox Manager

`asm` executes restricted declarative file jobs in independent in-memory filesystems. It supports write, read and delete, rejects unsafe paths and resource overages, and records exact outcomes. It never launches shell commands, Python code, containers, or external processes. This is a useful narrow interpreter, not an operating-system sandbox for arbitrary agents.

## Quickstart

Python 3.10 or later. CPU only, standard library runtime, no network access or model calls. Install from locally available packaging tools:

```powershell
python -m pip install --no-index --no-build-isolation --no-deps -e .
asm fixtures --out demo
asm run --input demo
asm report --format md
python -m pytest -q
```

If pip warns that its Scripts directory is not on PATH, add the displayed directory to your user PATH or use the module invocation below.

Offline alternative: replace `asm` with `python -m agent_sandbox_manager.cli`. pytest is a development dependency that must already be available locally. No random generator is used, so no seed is needed. The same input gives byte-identical result and report files. Execution duration is measured separately in build evidence and never inserted into deterministic reports.

## Input format

Use a directory containing JSON arrays or JSONL records (UTF-8). JSONL accepts comment lines starting with `#`. Files are processed by filename, results sorted by id. `expectations.json` is reserved sidecar metadata and is never executed. Markdown files are ignored. YAML and CSV are explicitly rejected: convert to the documented JSON schema. Empty directories produce zero counts.

```json
[{"id":"my-job","synthetic":false,"operations":[
  {"op":"write","path":"notes/result.txt","content":"hello"},
  {"op":"read","path":"notes/result.txt"}
]}]
```

`synthetic: false` means the author declares the job real. Henry can enter his own jobs by hand using this format; real trials and their results are not shipped. All records require exactly id, synthetic, operations. Ids are unique text, length 1 to 256. Operations are a list, maximum 1000 entries for parsing; execution permits 100 operations. Each operation requires op and path; write additionally requires content. Unknown operations yield a named policy denial; unknown fields yield a schema error. Dates and amounts are not supported fields, including negative amounts or future dates. They are rejected rather than silently interpreted.

Portable paths must be relative, at most 4096 characters, with no backslash, drive separator, empty component, dot component, parent component, NUL or control character. Windows absolute paths are accepted as input text then denied by policy. Unicode relative paths are supported. Content must be valid Unicode and at most 100000 characters. Live virtual file contents may total at most 65536 UTF-8 bytes. Overwrites replace prior byte usage; deletes release usage. Reads of absent files are denied. Every job starts empty. If any operation fails policy, all its virtual artifacts are discarded; completed_operations counts operations completed before rejection, not committed operations. Read does not expose any host data. No artifact is materialized to the host filesystem.

## Commands

- `asm fixtures --out demo`: generate the labelled 200-record dataset and independent hand-computed expectations.
- `asm run --input demo --state .asm/results.json`: validate and execute jobs, atomically save results, print JSON report.
- `asm report --format md --out report.md`: render the most recent results. Use `--format json` or `--state path` as needed.
- `asm validate --input demo`: schema validation plus a policy preview using the same deterministic interpreter; no result file is saved.
- `asm inspect --input demo --id job-000`: show one job's status and virtual artifacts with its provenance.

Each command offers `--help` with an example. Expected policy denials are successful analysis results, exit 0. Invalid inputs, missing jobs, parse failures and output failures return 2 with named errors. Parse errors include filename and line; JSON schema errors use line 1, JSONL schema errors use the record line. Duplicate ids name the offending id. Report output writes are atomic and clean up temporary files on failure. Run output is committed only after the whole input validates. Result files are local trusted artifacts, not cryptographically authenticated audit logs.

## Architecture

```text
JSON / JSONL -> cli.load_records -> core.workflow -> isolated core.execute
                                           |             |
                                           +-- results and exact totals
                                                     |
                              atomic local state <- cli -> report md/json
fixtures -> labelled records + independent expectations
```

The pure engine has no I/O, networking, clock or process execution. Host file access exists only in the CLI for declared input, state and output files. The CLI is not a sandbox for untrusted Python plugins. No OS security boundary is claimed. The input size is not globally bounded, so do not point it at huge untrusted directories. The in-memory interpreter enforces limits after parsing. Use a real OS sandbox if arbitrary programs or hostile large files must run.

## Honesty boundary and fixture policy

Every figure is computed from explicit records: job counts, denial reasons, committed UTF-8 bytes and operation counts. There are no predictions, time-saving claims or money-saving claims. Benefits remain unmeasured and no hypothetical benefit figures are presented. Reports state synthetic and author-declared real counts and explain that author identity is not verified. No real trial has been performed for this build.

JSON cannot carry header comments: expectations.json carries synthetic: true. jobs.jsonl carries both a SYNTHETIC comment and synthetic: true in every record. LABEL.md carries a SYNTHETIC header comment. The 200 records contain 120 successful two-byte writes, 20 path attacks, 20 unsupported commands, 15 byte overages, 15 operation overages, and 10 missing reads. Hand-computed totals: 200 jobs, 120 allowed, 80 denied, 240 committed bytes. Tests compare exact denied ids and totals against independent expectations. A corruption test changes a successful path to an attack and requires 81 denials and 238 bytes, demonstrating computation.

## Evidence and failure modes

See EVIDENCE.md for measured local test and demo results. Named parse, missing-input, schema and write errors have adversarial tests. Isolation, rollback, Unicode, long content, traversal, Windows paths, duplicate ids, empty inputs and deterministic bytes are tested. No arbitrary-code isolation claim is tested or made. Reports contain the per-record evidence needed to trace totals.

## Improvement hook and verdict

After two weeks of real use, Henry should record usage count and compare allowed/denied outcomes against a hand-checked sample. Primary metric: mismatched decisions divided by checked decisions. Record the sample, expected decisions, actual decisions, dates and measured error rate locally. If the rate exceeds 10 percent, fix the most frequent failure cause or kill with a recorded reason. If usage is zero, kill with that finding.

Verdict is pending the two-week evidence window, not invented at build time. Record it in VERDICT.md: expand for daily use or revenue, integrate for strong sibling overlap, commercialise for demonstrated buyer willingness, maintain for portfolio evidence otherwise, kill for no use or failed acceptance. Local synthetic correctness does not establish real-world demand.
