# Pokémon SoulGold PMD Animated Prototype — G3R11 Handoff

Date: 2026-08-29 (project timezone UTC+8)

## Scope authority

This handoff is ONLY for the **Pokémon SoulGold PMD Animated Prototype**.
Do not import gameplay/content assumptions from PMD AutoChess, Gen1recomp, Forest Symphony, or other projects.

Pinned authorities:

- SoulGold: `Eemeliri/soulgold`
- SoulGold revision: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- PMD SpriteCollab: `PMDCollab/SpriteCollab`
- SpriteCollab revision: `4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- Framework: `showpei1203/gen1recomp-optimization-features`
- Branch: `feature/pmd-portable-battle-framework`

## User-directed workflow rule

The user has explicitly deferred runtime testing for the current development sequence. Continue implementation and CI/build evidence without waiting for visual acceptance. **Do not convert build PASS into runtime visual PASS.**

Starting with this phase, every delivery must include an updated handoff containing exact commits, CI runs/jobs, artifacts, ROM hashes, unresolved defects, and the next implementation boundary.

## Preserved architecture

- Native SoulGold owns battle logic, status counters, move scripts, damage, targets, audio/FX, trainer/sendout choreography, health boxes, switching, and move timing.
- PMD owns only the battler body/shadow presentation layer for supported prototype species/actions.
- Native move presentation may preempt PMD presentation. PMD never blocks or changes native combat resolution.
- G3R4B OAM timing remains authoritative: PMD tick occurs after `AnimateSprites()` and before `BuildOamBuffer()`.
- Authentic PMDCollab shadow metadata/assets remain separate from PMD body frames.
- Known Cyndaquil ambient Idle single-frame ~1px downward sink remains unresolved and intentionally deferred.

## Special-state view authority

Do not force a category-wide 45-degree view for special states. Resolve view **per action** from the pinned PMDCollab `Anim.png`, `Offsets.png`, and `Shadow.png` geometry.

Pinned Cyndaquil/Marill findings:

- `Sleep`: `DIRECTIONLESS_SINGLE_ROW`; preserve source view, no forced UpRight/DownLeft.
- `EventSleep`: `DIRECTIONAL_8_ROWS`; use the requested battle row.
- `Wake`: `DIRECTIONAL_8_ROWS`; use the requested battle row.

This rule supersedes both simplistic policies: "all special states are directionless" and "all battle actions must be 45-degree".

## G3R10 — EventSleep entry transition

Build authority commit:
`9b78a3acf5d3510b02b759b8e94164b7dd784973`

Workflow:
`SoulGold PMD G3R10 Sleep Entry Transition Gate`

Run / job:
- Run `33207822146`
- Job `98973297192`
- Result: SUCCESS

Artifacts:
- ROM artifact ID `9700531943`
  - name `SoulGold-PMD-G3R10-ROM`
  - artifact ZIP digest `sha256:0dd4d3b6d4710571dd51c1a64f666e4320f188196403860b488ab135a819dd4a`
- Evidence artifact ID `9700530742`
  - name `soulgold-pmd-g3r10-build-evidence`
  - artifact ZIP digest `sha256:f27edca4fcaeb53ddfe9ba2439727c14f29f7dc7abfbcf98b7f7824718c7dff7`

G3R10 ROM:
- file `SoulGold-PMD-G3R10.gba`
- bytes `33554432`
- SHA-256 `1984deef3ad887b49d298523824b5e1c2ea0750ac66302704c46a6b01cd6982e`
- CRC32 `19583879`

G3R10 semantics:
- native `STATUS1_SLEEP` false->true observation queues PMDCollab `EventSleep`.
- EventSleep does not fight SoulGold `gDoingBattleAnim`; it waits/yields while native animation is busy.
- EventSleep is one-shot, then hands ownership to persistent PMDCollab `Sleep`.
- persistent Sleep remains directionless source authority.
- Wake body/shadow assets became source-ready, but G3R10 intentionally did not runtime-hook Wake.

## G3R11 — exact native Wake notification bridge

Build authority commit:
`a5879ab0d785e246b1685a4008c7e04f442e135a`

Implementation commit before workflow:
`2f5963a28d93b64f8cae248cb45504882ef3eb92`

Workflow:
`SoulGold PMD G3R11 Native Wake Notify Gate`

Run / job:
- Run `33208124936`
- Job `98974329564`
- Result: SUCCESS

Artifacts:
- ROM artifact ID `9700655785`
  - name `SoulGold-PMD-G3R11-ROM`
  - artifact ZIP digest `sha256:d70ea3b3916e13f3e7fb5e5ed89f2edfa52ee518dd677f08d67093a48af0c18d`
- Evidence artifact ID `9700654589`
  - name `soulgold-pmd-g3r11-build-evidence`
  - artifact ZIP digest `sha256:1badb26dca6267c094e441818704c39f4f8035ed35ab7aa785ec66a6050388b8`

G3R11 ROM:
- file `SoulGold-PMD-G3R11.gba`
- bytes `33554432`
- SHA-256 `6cb832a05717831da195e3e9bec80180c6b6d4708cd4df8678841936443b781d`
- CRC32 `97026E67`

G3R11 native source authority:
- pinned SoulGold clears sleep in `CancelerAsleepOrFrozen` before invoking `BattleScript_MoveUsedWokeUp`.
- pinned wake battle script prints the native wake message, waits, updates the status icon, then returns.
- G3R11 patches exactly two native wake paths in that canceler: ordinary timer wake and Uproar wake.
- both paths call `PmdSoulGoldPrototype_NotifyWake()` only after native SoulGold has cleared `STATUS1_SLEEP`.

G3R11 presentation semantics:
- new `PMD_PHASE_WAKE`.
- PMDCollab Wake body + authentic frame-synchronous shadow are bound from the action-specific directional source row.
- Wake is presentation-only and non-blocking. SoulGold does not wait for PMD Wake completion.
- native `BattleScript_MoveUsedWokeUp` remains unchanged and authoritative.
- if Wake finishes before the move, it returns HOME then ambient.
- if native move presentation begins first, existing Attack/Shoot ownership preempts Wake cleanly. No stale Wake resume.
- other sleep-cure paths are intentionally NOT hooked yet.

## Current validation state

Structural / build:
- G3R10 CI: PASS
- G3R11 CI: PASS
- PMD source warning/error gate: PASS
- ELF symbol gate: PASS
- ROM size gate: PASS

Runtime / visual:
- `PENDING_USER_DEFERRED_TESTING`
- Do not claim EventSleep, persistent Sleep, or Wake visual PASS until later AYN THOR -> RetroArch -> mGBA runtime acceptance.

Known unresolved visual defect:
- Cyndaquil ambient Idle has a single-frame ~1px downward sink.
- status: `DEFERRED_ROOT_CAUSE_UNRESOLVED`
- Do not hide, rename, or claim this defect fixed in later handoffs unless runtime evidence proves it.

## Next development boundary — G3R12

Proceed without waiting for user runtime testing.

Recommended narrow scope:

1. Audit **all remaining exact native ways sleep can be removed** outside the two `CancelerAsleepOrFrozen` paths, including move/item/ability/status-cure flows.
2. Add Wake presentation notifications only at source-grounded native message/transition points. Never infer Wake merely because `STATUS1_SLEEP` became zero after the fact.
3. Preserve the G3R11 non-blocking rule: PMD Wake may accompany native messaging but must never delay a move, status cure, switch, or battle script.
4. Keep unsupported status conditions native-only unless PMDCollab supplies an unambiguous semantic action. Do NOT relabel generic actions such as `Pain`, `Trip`, or `Laying` as poison/burn/paralysis/freeze without source authority.
5. Produce a new CI/ROM/evidence package and a new handoff even if runtime testing remains deferred.

## Do-not-regress gates

- pinned source revisions unchanged unless a later handoff explicitly promotes new pins.
- native trainer/sendout/switch/healthbox choreography unchanged.
- `AnimateSprites -> PMD Tick -> BuildOamBuffer` timing preserved.
- authentic PMDCollab body/shadow metadata used; no arbitrary recentering that causes body bobbing.
- PMD `Shadow.png` never drives body vertical motion.
- move/Hurt presentation priority remains above persistent/special-state presentation.
- special-state source view is per-action, not a global 45-degree rule.
- no runtime visual PASS without human/device evidence.
