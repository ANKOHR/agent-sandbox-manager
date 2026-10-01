import pytest
from agent_sandbox_manager.core import InputError, execute, workflow


def job(ops=None, **changes):
    return {"id": "one", "synthetic": False, "operations": ops or [], **changes}


@pytest.mark.parametrize("path", ["../secret", "/etc/passwd", "C:\\Windows\\file", "a/../b", "a//b", "a\x00b"])
def test_rejects_adversarial_values(path):
    assert execute(job([{"op": "write", "path": path, "content": "x"}]))["reason"] == "unsafe_path"


def test_duplicate_ids():
    with pytest.raises(InputError, match="duplicate id"):
        workflow([job(), job()])


@pytest.mark.parametrize("extra", [{"amount": -1}, {"date": "2099-01-01"}])
def test_schema_drift(extra):
    with pytest.raises(InputError, match="record.fields"):
        workflow([job(**extra)])


def test_handles_unicode_and_long_inputs():
    result = execute(job([{"op": "write", "path": "文档/é.txt", "content": "λ" * 30000}]))
    assert result["output_bytes"] == 60000
    assert result["status"] == "allowed"
    assert execute(job([{"op": "write", "path": "x", "content": "a" * 100000}]))["reason"] == "byte_limit"


def test_isolation_and_rollback():
    a = job([{"op": "write", "path": "a", "content": "x"}])
    b = job([{"op": "read", "path": "a"}], id="two")
    assert workflow([a,b])["results"][1]["reason"] == "missing_file"
    a["operations"].append({"op": "read", "path": "missing"})
    assert execute(a)["files"] == {}


def test_overwrite_delete_accounting():
    ops = [{"op": "write", "path": "a", "content": "x"},
           {"op": "write", "path": "a", "content": "é"},
           {"op": "delete", "path": "a"}]
    assert execute(job(ops))["output_bytes"] == 0
