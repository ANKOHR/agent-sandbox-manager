"""Reports compute no invented benefits."""
import json


def render(data, fmt="md"):
    summary = data["summary"]
    banner = (f"Provenance: {summary['synthetic_records']} synthetic fixture records; "
              f"{summary['real_records']} real records declared by the input author. "
              "Author identity and real-world provenance are not independently verified.")
    honesty = "Time saved and money saved: unmeasured; no benefit estimate is reported."
    scope = "Restricted declarative interpreter only; no arbitrary code or host process isolation."
    if fmt == "json":
        return json.dumps({**data, "provenance_banner": banner, "honesty": honesty,
                           "security_scope": scope}, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    lines = ["# Agent Sandbox Manager report", "", banner, "", scope, "", honesty, "",
             "## Computed counts", ""]
    for key in ("records", "allowed", "denied", "output_bytes"):
        lines.append(f"- {key}: {summary[key]}")
    lines.extend(["", "## Denial reasons", ""])
    for key, value in summary["denial_reasons"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Per-record evidence", "", "```json", json.dumps(data["results"],
                  ensure_ascii=True, sort_keys=True, indent=2), "```", ""])
    return "\n".join(lines).replace(chr(0x2014), "\\u2014")
