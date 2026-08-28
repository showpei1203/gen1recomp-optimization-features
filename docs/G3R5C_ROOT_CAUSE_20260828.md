# SoulGold PMD G3R5C Root Cause / Runtime Gate

Date: 2026-08-28

## Authority

- SoulGold: `Eemeliri/soulgold@b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- PMDCollab SpriteCollab: `PMDCollab/SpriteCollab@4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- Parent runtime result: G3R5B build PASS, human visual PARTIAL FAIL

## Human runtime symptoms after G3R5B

1. Cyndaquil still had one complete ambient action visually ~1 px below the accepted HOME/Idle battle baseline.
2. Static Idle0 PMD shadows did not follow the PMD body when an animation authored horizontal/vertical movement.

## Root cause 1: action-level ground registration

G3R5B fixed the video-proven Cyndaquil `Idle` frame 1 discontinuity only. It deliberately reset all other body presentation offsets to zero. That removed bad per-frame heuristics, but it also discarded a real *action-level* ground registration difference.

For Cyndaquil UpRight, normalized PMDCollab Shadow white-center Y deltas relative to Idle0 are:

- Idle: `[0, +1]`
- Walk: `[0, +1, 0, +1]`
- Nod: `[-1, -2, -1]`
- Rotate: `[0, -1, 0, -1, 0, -1, 0, 0, 0]`

The first, second, and fourth actions are centered around the Idle0 ground plane when the median is truncated toward zero. `Nod`, however, has median `-1`, so the entire action is registered one pixel below the accepted battle baseline after G3R4 green-body-center normalization.

G3R5C body rule:

- retain G3R4 per-frame green body-center normalization;
- derive one **constant** grounded-action correction from the median PMDCollab Shadow white-center delta;
- never copy Shadow.png's per-frame movement directly into the body;
- retain only explicit human-runtime micro overrides for intra-action defects.

Result for Cyndaquil:

- Idle body offsets: `[0, -1]` (frame 1 is the existing human-runtime correction)
- Walk: `[0, 0, 0, 0]`
- Nod: `[-1, -1, -1]`
- Rotate: all zero

Marill needs no action-level body correction for the selected ambient actions.

## Root cause 2: shadow timeline was collapsed to Idle0

PMDCollab supplies a separate `*-Shadow.png` timeline for every animation. The white marker is shadow position and the colored mask components encode the shadow. G3R5/G3R5B extracted only an Idle0 shadow for battle use, so the body timeline and shadow timeline were no longer synchronized.

G3R5C replaces the static shadow with a frame-synchronous shadow atlas:

- every selected action/frame uses its corresponding authentic `*-Shadow.png` component mask;
- each shadow frame stores the normalized white-center delta from Idle0;
- Idle0 X is calibrated to `0` so the player shadow remains centered on SoulGold battler base X;
- the current shadow frame is selected from the same runtime body frame index.

Runtime rendered relation:

`shadow = body base (x,y) + current body presentation (x2,y2) + PMDCollab frame shadow offset`

Thus authored left/right/up/down PMD movement moves the shadow in the same rendered coordinate system, while the PMDCollab frame still controls relative shadow placement and mask shape.

## Ownership / regression constraints

- G3R4B software tick order remains `AnimateSprites -> PMD Tick -> BuildOamBuffer -> RunTasks`.
- PMD shadow hides when PMD body ownership is not presenting.
- SoulGold native opponent shadow is restored outside PMD ownership.
- Save structures are unchanged.
- Attack/Hurt integration remains blocked until this body + shadow baseline receives human runtime acceptance.

## G3R5C CI

- Workflow: `SoulGold PMD G3R5C Dynamic Shadow Gate`
- Run: `33176168476`
- Framework commit used by build: `efc037a604d8fabe6a1785fd73a86f6f324d5fb8`
- Result: PASS
- ROM size: 33,554,432 bytes
- ROM SHA-256: `d8a28f6a3d4eb8d1270254e58dd26095c53935f05f01ba4002f9203914205050`
- ROM CRC32: `99EEBF14`
- Runtime visual status: **PENDING USER ACCEPTANCE**
