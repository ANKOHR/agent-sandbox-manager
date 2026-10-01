import json
import time
from pathlib import Path
from agent_sandbox_manager.cli import main


def test_run_completes_on_fixture(tmp_path, capsys):
    start = time.perf_counter()
    assert main(["fixtures", "--out", str(tmp_path / "demo")]) == 0
    assert main(["run", "--input", str(tmp_path / "demo"), "--state", str(tmp_path / "state.json")]) == 0
    assert main(["report", "--state", str(tmp_path / "state.json")]) == 0
    assert time.perf_counter() - start < 5
    assert "Provenance" in capsys.readouterr().out


def test_empty_input_renders_without_traceback(tmp_path, capsys):
    state = str(tmp_path / "state")
    assert main(["run", "--input", str(tmp_path), "--state", state]) == 0
    assert main(["report", "--state", state, "--format", "json"]) == 0
    assert '"records": 0' in capsys.readouterr().out


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "broken.jsonl").write_text('# SYNTHETIC\n{"broken"\n')
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "broken.jsonl: line 2" in error
    assert "Traceback" not in error


def test_determinism_byte_identical(tmp_path, capsys):
    main(["fixtures", "--out", str(tmp_path / "input")])
    state = tmp_path / "state.json"
    args = ["run", "--input", str(tmp_path / "input"), "--state", str(state)]
    main(args)
    first = state.read_bytes()
    main(args)
    assert state.read_bytes() == first
    main(["report", "--state", str(state), "--out", str(tmp_path / "a.md")])
    main(["report", "--state", str(state), "--out", str(tmp_path / "b.md")])
    assert (tmp_path / "a.md").read_bytes() == (tmp_path / "b.md").read_bytes()


def test_cli_smoke_all_subcommands(tmp_path, capsys):
    import pytest
    for cmd in ["fixtures", "run", "report", "validate", "inspect"]:
        with pytest.raises(SystemExit) as exc:
            main([cmd, "--help"])
        assert exc.value.code == 0
    main(["fixtures", "--out", str(tmp_path)])
    assert main(["validate", "--input", str(tmp_path)]) == 0
    assert main(["inspect", "--input", str(tmp_path), "--id", "job-000"]) == 0


def test_missing_input(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "absent")]) == 2
    assert "MissingInput" in capsys.readouterr().err


def test_report_write_failure_no_partial(tmp_path, capsys):
    state = tmp_path / "state.json"
    main(["run", "--input", str(tmp_path), "--state", str(state)])
    before = sorted(p.name for p in tmp_path.iterdir())
    assert main(["report", "--state", str(state), "--out", str(tmp_path)]) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == before
    assert "WriteError" in capsys.readouterr().err


def test_bad_result_schema(tmp_path, capsys):
    state = tmp_path / "state.json"
    state.write_text("{}")
    assert main(["report", "--state", str(state)]) == 2
    assert "ResultSchemaError" in capsys.readouterr().err
