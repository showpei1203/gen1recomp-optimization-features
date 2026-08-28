# SoulGold PMD G3R4 Regression Recovery Authority

Date: 2026-08-28
Status: ACTIVE CANDIDATE / COMPILE AND HUMAN RUNTIME ACCEPTANCE REQUIRED

## Why G3R4 exists

G3R3 compiled and passed static/ELF gates but was rejected by direct mGBA runtime video evidence from the user.

Observed in `mGBA - POKEMON EMER (59.8 fps) - 0.10.5 2026-08-28 17-59-45.mp4`:

1. Player Cyndaquil visibly entered battle using the legacy SoulGold battle body before PMD later took over.
2. Opponent Marill remained the native SoulGold battle sprite throughout the observed battle instead of becoming PMD.
3. Player PMD Cyndaquil still showed visually unacceptable whole-body vertical bobbing during ambient presentation.

Therefore G3R3 is **RUNTIME FAIL / NOT A BASELINE / NOT PROMOTABLE** regardless of its successful CI run.

## Root-cause correction A — RAM prime is not OBJ presentation

G3R3 decompressed PMD HOME into the battler/template backing `SpriteFrameImage` memory before `CreateSprite`, but did not explicitly copy PMD HOME into the newly-created sprite's OBJ VRAM.

This distinction is now formal:

**Backing image RAM ownership does not prove first-visible OBJ pixel ownership.**

G3R4 adds a post-create presentation gate after each authoritative normal battler `StartSpriteAnim(..., 0)` path:

`PmdSoulGoldPrototype_PrimeCreatedSpriteBody(battler, species)`

The adapter validates species/side through the profile, re-primes both backing slots, then queues:

`RequestSpriteFrameImageCopy(0, sprite->oam.tileNum, sprite->images)`

The hook must run before native send-out code later makes the sprite visible. Native send-out motion/timing remains SoulGold ownership.

## Root-cause correction B — opponent callback identity is not an ownership gate

G3R3 `CanPresentBattler` accepted only `SpriteCallbackDummy` or `SpriteCallbackDummy_2`.

That was too strict. Opponent front sprites may retain a native species-animation callback even after the battle reaches move selection. A callback-name whitelist can therefore deny PMD ownership forever even though no move/status/special animation is active.

G3R4 removes callback identity from the move-selection PMD gate.

The runtime gate remains strict through:

- `InBattleChoosingMoves()`
- valid/in-use/visible battler sprite
- canonical battler `frameImages[position]`
- `!gDoingBattleAnim`
- no `animFromTableActive`
- no `specialAnimActive`
- no `statusAnimActive`

## Root-cause correction C — reject fused body+shadow grounding for the recovered body path

The G3R2/G3R3 experiment fixed the whole PMD body+shadow tile to PMD shadow/ground authority. Runtime evidence showed that raw PMD internal body motion then reads as battlefield bobbing in SoulGold's 45-degree battle view.

G2's body-only green body-center normalization had already produced a visually steadier accepted body presentation.

G3R4 therefore restores:

`PMD_BODY_CENTER_PER_FRAME_G2_RESTORED`

for the body OBJ.

Every emitted body frame aligns its PMD green `Offsets.png` body-center marker to the species battle anchor. Runtime `presentationX/Y` remain zero.

The previous atomic body+shadow contract is revoked for this prototype's grounded battle presentation.

G3R4 body frames contain **no PMD shadow pixels**. PMD ground shadow is deferred to a separate ground layer/OBJ after the body regression recovery is visually accepted.

This is not removal of the shadow requirement. It is separation of two presentation authorities that must not move as one object.

## G3R4 target registry

- Cyndaquil + player side: PMD `UpRight`
- Marill + opponent side: PMD `DownLeft`
- all other species/side combinations: native SoulGold, untouched

Ambient set:

`HOME -> Idle -> HOME -> Walk -> HOME -> Nod -> HOME -> Rotate -> HOME`

`Pose`, `LookUp`, `DeepBreath`, `Sit` remain excluded.

## Anti-regression gates

G3R4 CI must reject the candidate unless:

- exactly two normal battler template-prime hooks exist in `battle_controllers.c`;
- exactly two post-created-sprite OBJ-VRAM prime hooks exist;
- `RequestSpriteFrameImageCopy` is linked through the created-sprite prime;
- the PMD adapter contains no Dummy-callback ownership whitelist;
- both Cyndaquil and Marill action symbols are linked;
- manifests declare G2-restored body-center authority;
- manifests declare `included_in_body_frames=false` for shadow;
- all body frames resolve their green source center to the declared anchor;
- runtime presentation offsets are zero;
- `MAX_MON_PIC_FRAMES` plumbing remains unchanged;
- native `sprite->anims` ownership remains unchanged;
- save-format plumbing remains unchanged.

## Human acceptance gate

Compile PASS is insufficient.

G3R4 is accepted only if the user's fresh-boot mGBA test confirms all of the following:

1. Player Cyndaquil's first visible Pokémon body is PMD, with no legacy battle-body flash.
2. Opponent Marill's first visible Pokémon body is PMD.
3. Marill remains PMD during move selection and participates in PMD ambient presentation.
4. Cyndaquil no longer exhibits the G3R3 whole-body vertical bob regression.
5. Native send-out motion/timing remains intact.
6. Native move ownership still yields and returns to HOME correctly.
7. No body corruption, palette corruption, tearing, or save incompatibility occurs.

Only after these pass should separate PMD ground-shadow rendering be added.

## User reference ROM

`Pokemon-SoulGold-v1.gba`

- bytes: `33554432`
- SHA-256: `a22aa2bbcaa9953f15d9abc2ef1069d4a082fab059d701781e5b83ff376c1f9d`
- CRC32: `15E8D557`
- GBA title: `POKEMON EMER`
- game code: `BPEE`
- maker: `01`
- version: `0`

Classification: `USER_REFERENCE_ROM`. It is not a destructive patch base and does not replace the pinned SoulGold source authority.
