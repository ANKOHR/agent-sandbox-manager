import json
from agent_sandbox_manager.fixtures import generate, records, expectations
from agent_sandbox_manager.core import workflow


def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path / "jobs.jsonl").read_text(encoding="utf-8").startswith("# SYNTHETIC")
    assert all(r["synthetic"] is True for r in records())
    assert json.loads((tmp_path / "expectations.json").read_text())["synthetic"] is True
    assert "SYNTHETIC" in (tmp_path / "LABEL.md").read_text()


def test_fixture_ground_truth_matches_hand_computed():
    assert workflow(records())["summary"] == expectations()["summary"]


def test_corrupted_fixture_changes_figures():
    changed = records()
    changed[0]["operations"][0]["path"] = "../escape"
    result = workflow(changed)
    assert result["summary"]["denied"] == 81
    assert result["summary"]["output_bytes"] == 238
