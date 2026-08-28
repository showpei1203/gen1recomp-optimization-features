#include "global.h"
#include "battle.h"
#include "battle_util.h"
#include "sprite.h"
#include "constants/species.h"
#include "pmd_gba_runtime.h"
#include "pmd_soulgold_adapter.h"
#include "pmd_soulgold_prototype.h"

extern const struct PmdGbaAction gPmdCyndaquilPlayerHomeAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerIdleAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerWalkAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerNodAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerPoseAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerRotateAction;

extern const struct PmdGbaAction gPmdCyndaquilOpponentHomeAction;
extern const struct PmdGbaAction gPmdCyndaquilOpponentIdleAction;
extern const struct PmdGbaAction gPmdCyndaquilOpponentWalkAction;
extern const struct PmdGbaAction gPmdCyndaquilOpponentNodAction;
extern const struct PmdGbaAction gPmdCyndaquilOpponentPoseAction;
extern const struct PmdGbaAction gPmdCyndaquilOpponentRotateAction;

enum PmdAmbientPhase
{
    PMD_AMBIENT_HOME,
    PMD_AMBIENT_ACTION,
};

struct PmdCyndaquilAmbientState
{
    bool8 initialized;
    u8 spriteId;
    u8 sequenceIndex;
    u8 phase;
    u16 homeTicksLeft;
};

#define CYND_AMBIENT_ACTION_COUNT 5

static struct PmdCyndaquilAmbientState sAmbient[PMD_GBA_MAX_BATTLERS];

// Every selected G3 action has a genuine directional PMD sheet. HOME uses the
// approved 45-degree row. Transitional turning is allowed when the action
// naturally settles back to HOME, therefore Rotate remains valid.
static const u16 sCyndaquilHomeHolds[CYND_AMBIENT_ACTION_COUNT] =
{
    28, // Idle
    18, // Walk
    24, // Nod
    30, // Pose
    24, // Rotate
};

static const struct PmdGbaAction *GetHomeAction(u8 battler)
{
    return GetBattlerSide(battler) == B_SIDE_PLAYER
        ? &gPmdCyndaquilPlayerHomeAction
        : &gPmdCyndaquilOpponentHomeAction;
}

static const struct PmdGbaAction *GetAmbientAction(u8 battler, u8 sequenceIndex)
{
    bool32 player = GetBattlerSide(battler) == B_SIDE_PLAYER;

    switch (sequenceIndex % CYND_AMBIENT_ACTION_COUNT)
    {
    case 0:
        return player ? &gPmdCyndaquilPlayerIdleAction : &gPmdCyndaquilOpponentIdleAction;
    case 1:
        return player ? &gPmdCyndaquilPlayerWalkAction : &gPmdCyndaquilOpponentWalkAction;
    case 2:
        return player ? &gPmdCyndaquilPlayerNodAction : &gPmdCyndaquilOpponentNodAction;
    case 3:
        return player ? &gPmdCyndaquilPlayerPoseAction : &gPmdCyndaquilOpponentPoseAction;
    default:
        return player ? &gPmdCyndaquilPlayerRotateAction : &gPmdCyndaquilOpponentRotateAction;
    }
}

static void ClearAmbient(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;

    PmdGbaRuntime_Unbind(battler);
    sAmbient[battler].initialized = FALSE;
    sAmbient[battler].spriteId = SPRITE_NONE;
    sAmbient[battler].sequenceIndex = 0;
    sAmbient[battler].phase = PMD_AMBIENT_HOME;
    sAmbient[battler].homeTicksLeft = 0;
}

static void BindHome(u8 battler, u16 holdTicks, bool32 restartSequence)
{
    struct PmdCyndaquilAmbientState *state = &sAmbient[battler];

    if (restartSequence)
        state->sequenceIndex = 0;

    if (!PmdGbaRuntime_Bind(battler, GetHomeAction(battler)))
    {
        ClearAmbient(battler);
        return;
    }

    state->initialized = TRUE;
    state->spriteId = gBattlerSpriteIds[battler];
    state->phase = PMD_AMBIENT_HOME;
    state->homeTicksLeft = holdTicks;
}

static void BindCurrentAmbientAction(u8 battler)
{
    struct PmdCyndaquilAmbientState *state = &sAmbient[battler];

    if (!PmdGbaRuntime_Bind(battler, GetAmbientAction(battler, state->sequenceIndex)))
    {
        BindHome(battler, 28, TRUE);
        return;
    }

    state->phase = PMD_AMBIENT_ACTION;
}

void PmdSoulGoldPrototype_PrimeBattlerBody(u8 battler)
{
    const struct PmdGbaAction *home;

    if (battler >= gBattlersCount)
        return;
    if (GetBattlerVisualSpecies(battler) != SPECIES_CYNDAQUIL)
        return;

    home = GetHomeAction(battler);
    if (home == NULL || home->frames == NULL || home->frameCount == 0)
        return;

    // The HOME frame already contains the authentic PMD shadow underneath the
    // body, so send-out priming starts with the same visual contract as ambient.
    PmdSoulGold_PrimeBodyFrame(battler, &home->frames[0]);
}

void PmdSoulGoldPrototype_Init(void)
{
    u8 battler;

    PmdSoulGold_Init();
    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        sAmbient[battler].initialized = FALSE;
        sAmbient[battler].spriteId = SPRITE_NONE;
        sAmbient[battler].sequenceIndex = 0;
        sAmbient[battler].phase = PMD_AMBIENT_HOME;
        sAmbient[battler].homeTicksLeft = 0;
    }
}

void PmdSoulGoldPrototype_Tick(void)
{
    u8 battler;

    PmdGbaRuntime_Tick();

    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        struct PmdCyndaquilAmbientState *state = &sAmbient[battler];
        u16 species;
        u8 spriteId;

        if (battler >= gBattlersCount)
        {
            ClearAmbient(battler);
            continue;
        }

        species = GetBattlerVisualSpecies(battler);
        spriteId = gBattlerSpriteIds[battler];

        if (species != SPECIES_CYNDAQUIL)
        {
            ClearAmbient(battler);
            continue;
        }

        if (state->initialized && state->spriteId != spriteId)
        {
            ClearAmbient(battler);
            state = &sAmbient[battler];
        }

        if (PmdGbaRuntime_ConsumeInterrupted(battler))
        {
            BindHome(battler, 28, TRUE);
            continue;
        }

        if (!state->initialized)
        {
            BindHome(battler, 28, TRUE);
            continue;
        }

        if (state->phase == PMD_AMBIENT_HOME)
        {
            if (!PmdGbaRuntime_IsPresenting(battler))
                continue;

            if (state->homeTicksLeft > 0)
            {
                state->homeTicksLeft--;
                continue;
            }

            BindCurrentAmbientAction(battler);
            continue;
        }

        if (state->phase == PMD_AMBIENT_ACTION && PmdGbaRuntime_IsComplete(battler))
        {
            u8 completedIndex = state->sequenceIndex % CYND_AMBIENT_ACTION_COUNT;
            state->sequenceIndex = (state->sequenceIndex + 1) % CYND_AMBIENT_ACTION_COUNT;
            BindHome(battler, sCyndaquilHomeHolds[completedIndex], FALSE);
        }
    }
}

void PmdSoulGoldPrototype_Reset(void)
{
    u8 battler;

    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
        ClearAmbient(battler);
    PmdSoulGold_Reset();
}
