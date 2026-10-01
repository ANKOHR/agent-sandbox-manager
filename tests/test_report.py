import json
from agent_sandbox_manager.fixtures import records, expectations
from agent_sandbox_manager.core import workflow
from agent_sandbox_manager.report import render


def test_report_matches_ground_truth_exact():
    assert json.loads(render(workflow(records()), "json"))["summary"] == expectations()["summary"]


def test_report_zero_false_positives():
    results = json.loads(render(workflow(records()), "json"))["results"]
    assert [r["id"] for r in results if r["status"] == "denied"] == expectations()["denied_ids"]


def test_report_carries_provenance_banner():
    for fmt in ("md", "json"):
        assert "Provenance: 200 synthetic fixture records; 0 real records" in render(workflow(records()), fmt)


def test_hypothetical_figures_labelled():
    for fmt in ("md", "json"):
        assert "unmeasured; no benefit estimate" in render(workflow([]), fmt)


def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(workflow(records()), fmt)


def test_em_dash_input_escaped_in_reports():
    data = workflow([{"id": "job" + chr(0x2014), "synthetic": False, "operations": [
        {"op": "write", "path": "a", "content": chr(0x2014)}]}])
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(data, fmt)
    assert json.loads(render(data, "json"))["results"][0]["files"]["a"] == chr(0x2014)
