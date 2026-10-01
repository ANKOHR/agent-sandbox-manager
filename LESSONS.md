# Lessons for KOML

The domain requires naming the isolation boundary before implementing execution. A restricted declarative interpreter can guarantee that its operations never access host paths; path checks alone would not safely confine arbitrary Python or shell commands.

Validated by synthetic evidence: independent per-job virtual state, rollback on denial, exact UTF-8 accounting and deterministic reports match planted outcomes. Broken assumption: a generic sandbox manager can safely run arbitrary agent code using only portable standard-library path validation. This build therefore supports a deliberately restricted job language. Real-world usefulness remains untested.

Operating rule: specify the threat model and executable language first, then require independent expected decisions and a mutation test before claiming correctness. Never infer OS isolation from a passing path traversal test.
