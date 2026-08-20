# Collector Session-Safe V2

This is a test-tool correction only. Runtime/MOD files are unchanged.

## Defect 1: cross-process id collision

Original analyzer keyed ACTION_BIND rows only by `id`. Android app restart resets the runtime counter, so logcat buffers containing more than one app process can have duplicate ids. In the 2026-08-20 17:01 evidence, PID 7088 THUNDERSHOCK HIT ids 1/2/4 were incorrectly matched to PID 7831 non-damage status START ids 1/2/4.

V2 identity is `PID + id`. Multi-hit sequence identity is `PID + seq`.

## Defect 2: name-based projectile coverage

Original coverage treated `EMBER|GUST` as projectile by move name. Current GUST mapping is `family=strike`, `primary=contact`, `projectile=false`, so name-only coverage is invalid.

V2 requires actual semantic rows:
- contact: contact semantic row
- projectile: `projectile=true`
- multi: >=2 rows in one PID+seq
- sustained: sustainedCandidate with positive native audio tail
- status: nonDamageStatus row

## Artifact

ZIP SHA-256: `dd4f481b561da73b616967c02dd348835d7ab0038adc0f39ab0590da64231a13`
Drive ZIP: `1IpCXXa2n18TxxTcDp43dT4gZIUx8EIZu`

## Remaining closure

Exact v0.1.99b stays installed. Do not clear logcat. Execute Ember once and hit, then run the Session-Safe V2 collector. Current evidence already contains healthy Contact, Multi, Sustained, and Status semantics.
