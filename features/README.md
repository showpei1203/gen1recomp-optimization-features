# Feature Lane

Scope:
- new gameplay mechanics
- new presentation / UI behavior
- new MOD-backed capabilities
- new quality-of-life features

Rules:
- develop independently from optimization changes first
- document dependencies and conflicts
- do not silently take over Start / Select or other shared input authority
- every feature needs disable / rollback semantics where feasible
