# M2R11C VALIDATOR DRIFT PREVENTION AUTHORITY

## Problem
A current implementation can deliberately supersede an older presentation contract while an older static validator still searches for the removed token. This creates false FAILs before build. This failure class has repeated enough times that it is now treated as a release-process bug.

## Mandatory rule
Before any Handoff is released after a semantic change:
1. assign a new regression ID;
2. record any superseded regression in `SOULGOLD_VALIDATOR_CONTRACTS_M2R11C.tsv`;
3. update the active current-contract validator owner;
4. current stage scripts must call `validate_current_presentation_contract.py`, not rely on a historical semantic gate alone;
5. `validate_validator_contracts.py` must PASS;
6. all regression log lines must be independently and correctly quoted;
7. run the complete static prebuild sequence actually used by the launcher before packaging.

## Current supersession
R-SD-024 (healthbox occluder only during opponent faint motion) is superseded by R-SD-039 (player healthbox always above opponent front).

## New meta-regression
R-SD-040: ACTIVE_VALIDATORS_MUST_TRACK_CURRENT_SEMANTICS_AND_SUPERSESSIONS.
