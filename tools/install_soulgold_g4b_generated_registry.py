#!/usr/bin/env python3
"""Install G4B generated PMD species registry with explicit native fallback.

G3R11 still stores two prototype profiles directly in pmd_soulgold_prototype.c.
That does not scale to a National Dex. G4B moves profile lookup behind a
registry module without activating any new species yet.

The critical contract is explicit:
- registry hit for exact SoulGold species + side -> PMD presentation profile
- registry miss -> NULL -> existing SoulGold native battler sprite stays owner

This gate intentionally retains only the already-proven Cyndaquil/player and
Marill/opponent entries. G4C will feed generated entries/assets from audited
PMDCollab coverage instead of turning a two-entry proof into a thousand-line
hand-maintained switch statement, a fate no source file deserves.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


REGISTRY_H = r'''#ifndef GUARD_PMD_SOULGOLD_SPECIES_REGISTRY_H
#define GUARD_PMD_SOULGOLD_SPECIES_REGISTRY_H

#include "global.h"
#include "pmd_gba_runtime.h"
#include "pmd_soulgold_dynamic_shadow.h"

#define PMD_SOULGOLD_AMBIENT_COUNT 4
/* Compatibility alias for the already-audited G3 runtime loops. */
#define PMD_G3R6B_AMBIENT_COUNT PMD_SOULGOLD_AMBIENT_COUNT

struct PmdSpeciesProfile
{
    u16 species;
    u8 side;
    const struct PmdGbaAction *home;
    const struct PmdGbaAction *ambient[PMD_SOULGOLD_AMBIENT_COUNT];
    const struct PmdGbaAction *hurt;
    const struct PmdGbaAction *attack;
    const struct PmdGbaAction *shoot;
    const struct PmdGbaAction *sleep;
    const struct PmdGbaAction *eventSleep;
    const struct PmdGbaAction *wake;
    const struct PmdSoulGoldShadowAction *shadowHome;
    const struct PmdSoulGoldShadowAction *shadowAmbient[PMD_SOULGOLD_AMBIENT_COUNT];
    const struct PmdSoulGoldShadowAction *shadowHurt;
    const struct PmdSoulGoldShadowAction *shadowAttack;
    const struct PmdSoulGoldShadowAction *shadowShoot;
    const struct PmdSoulGoldShadowAction *shadowSleep;
    const struct PmdSoulGoldShadowAction *shadowEventSleep;
    const struct PmdSoulGoldShadowAction *shadowWake;
    const u8 *attackRushFrame;
    const u8 *attackHitFrame;
    const u8 *attackReturnFrame;
    const u8 *shootRushFrame;
    const u8 *shootHitFrame;
    const u8 *shootReturnFrame;
    u16 homeHolds[PMD_SOULGOLD_AMBIENT_COUNT];
};

const struct PmdSpeciesProfile *PmdSoulGoldSpeciesRegistry_Find(u16 species, u8 side);
u16 PmdSoulGoldSpeciesRegistry_Count(void);

#endif // GUARD_PMD_SOULGOLD_SPECIES_REGISTRY_H
'''

REGISTRY_C = r'''/* G4B generated-registry proof. G4C replaces entries from audited manifests. */
#include "global.h"
#include "constants/battle.h"
#include "constants/species.h"
#include "pmd_soulgold_species_registry.h"

extern const struct PmdGbaAction gPmdCyndaquilPlayerHomeAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerIdleAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerWalkAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerNodAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerRotateAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerHurtAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerAttackAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerShootAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerSleepAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerEventSleepAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerWakeAction;
extern const u8 gPmdCyndaquilPlayerAttackRushFrame;
extern const u8 gPmdCyndaquilPlayerAttackHitFrame;
extern const u8 gPmdCyndaquilPlayerAttackReturnFrame;
extern const u8 gPmdCyndaquilPlayerShootRushFrame;
extern const u8 gPmdCyndaquilPlayerShootHitFrame;
extern const u8 gPmdCyndaquilPlayerShootReturnFrame;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerHomeShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerIdleShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerWalkShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerNodShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerRotateShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerHurtShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerAttackShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerShootShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerSleepShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerEventSleepShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerWakeShadowAction;

extern const struct PmdGbaAction gPmdMarillOpponentHomeAction;
extern const struct PmdGbaAction gPmdMarillOpponentIdleAction;
extern const struct PmdGbaAction gPmdMarillOpponentWalkAction;
extern const struct PmdGbaAction gPmdMarillOpponentNodAction;
extern const struct PmdGbaAction gPmdMarillOpponentRotateAction;
extern const struct PmdGbaAction gPmdMarillOpponentHurtAction;
extern const struct PmdGbaAction gPmdMarillOpponentAttackAction;
extern const struct PmdGbaAction gPmdMarillOpponentShootAction;
extern const struct PmdGbaAction gPmdMarillOpponentSleepAction;
extern const struct PmdGbaAction gPmdMarillOpponentEventSleepAction;
extern const struct PmdGbaAction gPmdMarillOpponentWakeAction;
extern const u8 gPmdMarillOpponentAttackRushFrame;
extern const u8 gPmdMarillOpponentAttackHitFrame;
extern const u8 gPmdMarillOpponentAttackReturnFrame;
extern const u8 gPmdMarillOpponentShootRushFrame;
extern const u8 gPmdMarillOpponentShootHitFrame;
extern const u8 gPmdMarillOpponentShootReturnFrame;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentHomeShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentIdleShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentWalkShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentNodShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentRotateShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentHurtShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentAttackShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentShootShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentSleepShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentEventSleepShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentWakeShadowAction;

static const struct PmdSpeciesProfile sPmdSpeciesProfiles[] =
{
    {
        .species = SPECIES_CYNDAQUIL,
        .side = B_SIDE_PLAYER,
        .home = &gPmdCyndaquilPlayerHomeAction,
        .ambient = { &gPmdCyndaquilPlayerIdleAction, &gPmdCyndaquilPlayerWalkAction, &gPmdCyndaquilPlayerNodAction, &gPmdCyndaquilPlayerRotateAction },
        .hurt = &gPmdCyndaquilPlayerHurtAction,
        .attack = &gPmdCyndaquilPlayerAttackAction,
        .shoot = &gPmdCyndaquilPlayerShootAction,
        .sleep = &gPmdCyndaquilPlayerSleepAction,
        .eventSleep = &gPmdCyndaquilPlayerEventSleepAction,
        .wake = &gPmdCyndaquilPlayerWakeAction,
        .shadowHome = &gPmdCyndaquilPlayerHomeShadowAction,
        .shadowAmbient = { &gPmdCyndaquilPlayerIdleShadowAction, &gPmdCyndaquilPlayerWalkShadowAction, &gPmdCyndaquilPlayerNodShadowAction, &gPmdCyndaquilPlayerRotateShadowAction },
        .shadowHurt = &gPmdCyndaquilPlayerHurtShadowAction,
        .shadowAttack = &gPmdCyndaquilPlayerAttackShadowAction,
        .shadowShoot = &gPmdCyndaquilPlayerShootShadowAction,
        .shadowSleep = &gPmdCyndaquilPlayerSleepShadowAction,
        .shadowEventSleep = &gPmdCyndaquilPlayerEventSleepShadowAction,
        .shadowWake = &gPmdCyndaquilPlayerWakeShadowAction,
        .attackRushFrame = &gPmdCyndaquilPlayerAttackRushFrame,
        .attackHitFrame = &gPmdCyndaquilPlayerAttackHitFrame,
        .attackReturnFrame = &gPmdCyndaquilPlayerAttackReturnFrame,
        .shootRushFrame = &gPmdCyndaquilPlayerShootRushFrame,
        .shootHitFrame = &gPmdCyndaquilPlayerShootHitFrame,
        .shootReturnFrame = &gPmdCyndaquilPlayerShootReturnFrame,
        .homeHolds = {28, 18, 24, 24},
    },
    {
        .species = SPECIES_MARILL,
        .side = B_SIDE_OPPONENT,
        .home = &gPmdMarillOpponentHomeAction,
        .ambient = { &gPmdMarillOpponentIdleAction, &gPmdMarillOpponentWalkAction, &gPmdMarillOpponentNodAction, &gPmdMarillOpponentRotateAction },
        .hurt = &gPmdMarillOpponentHurtAction,
        .attack = &gPmdMarillOpponentAttackAction,
        .shoot = &gPmdMarillOpponentShootAction,
        .sleep = &gPmdMarillOpponentSleepAction,
        .eventSleep = &gPmdMarillOpponentEventSleepAction,
        .wake = &gPmdMarillOpponentWakeAction,
        .shadowHome = &gPmdMarillOpponentHomeShadowAction,
        .shadowAmbient = { &gPmdMarillOpponentIdleShadowAction, &gPmdMarillOpponentWalkShadowAction, &gPmdMarillOpponentNodShadowAction, &gPmdMarillOpponentRotateShadowAction },
        .shadowHurt = &gPmdMarillOpponentHurtShadowAction,
        .shadowAttack = &gPmdMarillOpponentAttackShadowAction,
        .shadowShoot = &gPmdMarillOpponentShootShadowAction,
        .shadowSleep = &gPmdMarillOpponentSleepShadowAction,
        .shadowEventSleep = &gPmdMarillOpponentEventSleepShadowAction,
        .shadowWake = &gPmdMarillOpponentWakeShadowAction,
        .attackRushFrame = &gPmdMarillOpponentAttackRushFrame,
        .attackHitFrame = &gPmdMarillOpponentAttackHitFrame,
        .attackReturnFrame = &gPmdMarillOpponentAttackReturnFrame,
        .shootRushFrame = &gPmdMarillOpponentShootRushFrame,
        .shootHitFrame = &gPmdMarillOpponentShootHitFrame,
        .shootReturnFrame = &gPmdMarillOpponentShootReturnFrame,
        .homeHolds = {26, 18, 22, 24},
    },
};

const struct PmdSpeciesProfile *PmdSoulGoldSpeciesRegistry_Find(u16 species, u8 side)
{
    u16 i;
    for (i = 0; i < ARRAY_COUNT(sPmdSpeciesProfiles); i++)
    {
        if (sPmdSpeciesProfiles[i].species == species && sPmdSpeciesProfiles[i].side == side)
            return &sPmdSpeciesProfiles[i];
    }
    return NULL;
}

u16 PmdSoulGoldSpeciesRegistry_Count(void)
{
    return ARRAY_COUNT(sPmdSpeciesProfiles);
}
'''


def patch_prototype(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    include_anchor = '#include "pmd_soulgold_dynamic_shadow.h"\n'
    include_line = '#include "pmd_soulgold_species_registry.h"\n'
    if include_line not in text:
        if include_anchor not in text:
            raise SystemExit("G4B registry include anchor missing")
        text = text.replace(include_anchor, include_anchor + include_line, 1)

    struct_start = text.find("#define PMD_G3R6B_AMBIENT_COUNT 4\n\nstruct PmdSpeciesProfile\n{")
    state_start = text.find("struct PmdPresentationState\n{")
    if struct_start >= 0:
        if state_start < struct_start:
            raise SystemExit("G4B profile/state structure ordering changed")
        text = text[:struct_start] + text[state_start:]
    elif "struct PmdSpeciesProfile\n{" in text:
        raise SystemExit("G4B private profile structure still present without expected anchor")

    table_start = text.find("static const struct PmdSpeciesProfile sProfiles[] =\n{")
    state_storage = text.find("static struct PmdPresentationState sState[PMD_GBA_MAX_BATTLERS];")
    if table_start >= 0:
        if state_storage < table_start:
            raise SystemExit("G4B profile table/state storage ordering changed")
        text = text[:table_start] + text[state_storage:]
    elif "sProfiles[]" in text:
        raise SystemExit("G4B private profile table still present without expected anchor")

    find_start = text.find("static const struct PmdSpeciesProfile *FindProfile(u8 battler)\n{")
    if find_start < 0:
        raise SystemExit("G4B FindProfile anchor missing")
    find_end = text.find("\nstatic bool32", find_start)
    if find_end < 0:
        raise SystemExit("G4B FindProfile boundary missing")
    replacement = '''static const struct PmdSpeciesProfile *FindProfile(u8 battler)\n{
    if (battler >= gBattlersCount)
        return NULL;
    return PmdSoulGoldSpeciesRegistry_Find(GetBattlerVisualSpecies(battler), GetBattlerSide(battler));
}\n'''
    text = text[:find_start] + replacement + text[find_end:]
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    soulgold = args.soulgold.resolve()
    framework = args.framework_root.resolve()
    staging = args.assets_staging.resolve()

    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r11_wake_notify.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    (soulgold / "include" / "pmd_soulgold_species_registry.h").write_text(REGISTRY_H, encoding="utf-8")
    (soulgold / "src" / "pmd_soulgold_species_registry.c").write_text(REGISTRY_C, encoding="utf-8")
    patch_prototype(soulgold / "src" / "pmd_soulgold_prototype.c")

    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    reg = (soulgold / "src" / "pmd_soulgold_species_registry.c").read_text(encoding="utf-8")
    if "PmdSoulGoldSpeciesRegistry_Find(GetBattlerVisualSpecies(battler), GetBattlerSide(battler))" not in proto:
        raise SystemExit("G4B prototype does not delegate profile lookup to registry")
    if "static const struct PmdSpeciesProfile sProfiles[]" in proto:
        raise SystemExit("G4B old in-prototype table survived")
    if reg.count(".species = SPECIES_") != 2:
        raise SystemExit("G4B proof registry must preserve exactly two currently activated profiles")

    (soulgold / "PMD_G4B_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G4B generated species registry architecture installed.\n"
        "runtime_parent=G3R11\n"
        "registry_entries=2\n"
        "registry_entry_1=SPECIES_CYNDAQUIL,B_SIDE_PLAYER\n"
        "registry_entry_2=SPECIES_MARILL,B_SIDE_OPPONENT\n"
        "registry_miss_policy=RETURN_NULL_KEEP_NATIVE_SOULGOLD_BATTLER\n"
        "new_species_activated=0\n"
        "full_roster_activation=DEFERRED_TO_G4C_GENERATED_ASSETS\n"
        "form_mapping=NOT_GUESSED\n"
        "runtime_visual_status=PENDING_USER_DEFERRED_TESTING\n",
        encoding="utf-8",
    )
    print("G4B generated registry installer PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
