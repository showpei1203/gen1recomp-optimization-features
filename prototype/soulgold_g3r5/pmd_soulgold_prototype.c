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
extern const struct PmdGbaAction gPmdCyndaquilPlayerRotateAction;

extern const struct PmdGbaAction gPmdMarillOpponentHomeAction;
extern const struct PmdGbaAction gPmdMarillOpponentIdleAction;
extern const struct PmdGbaAction gPmdMarillOpponentWalkAction;
extern const struct PmdGbaAction gPmdMarillOpponentNodAction;
extern const struct PmdGbaAction gPmdMarillOpponentRotateAction;

enum PmdAmbientPhase
{
    PMD_AMBIENT_HOME,
    PMD_AMBIENT_ACTION,
};

#define PMD_G3R5_ACTION_COUNT 4

struct PmdSpeciesProfile
{
    u16 species;
    u8 side;
    const struct PmdGbaAction *home;
    const struct PmdGbaAction *actions[PMD_G3R5_ACTION_COUNT];
    u16 homeHolds[PMD_G3R5_ACTION_COUNT];
};

struct PmdAmbientState
{
    const struct PmdSpeciesProfile *profile;
    bool8 initialized;
    u8 spriteId;
    u8 sequenceIndex;
    u8 phase;
    u16 homeTicksLeft;
};

static const struct PmdSpeciesProfile sProfiles[] =
{
    {
        .species = SPECIES_CYNDAQUIL,
        .side = B_SIDE_PLAYER,
        .home = &gPmdCyndaquilPlayerHomeAction,
        .actions =
        {
            &gPmdCyndaquilPlayerIdleAction,
            &gPmdCyndaquilPlayerWalkAction,
            &gPmdCyndaquilPlayerNodAction,
            &gPmdCyndaquilPlayerRotateAction,
        },
        .homeHolds = {28, 18, 24, 24},
    },
    {
        .species = SPECIES_MARILL,
        .side = B_SIDE_OPPONENT,
        .home = &gPmdMarillOpponentHomeAction,
        .actions =
        {
            &gPmdMarillOpponentIdleAction,
            &gPmdMarillOpponentWalkAction,
            &gPmdMarillOpponentNodAction,
            &gPmdMarillOpponentRotateAction,
        },
        .homeHolds = {26, 18, 22, 24},
    },
};

static struct PmdAmbientState sAmbient[PMD_GBA_MAX_BATTLERS];

static const struct PmdSpeciesProfile *FindProfile(u8 battler)
{
    u16 species;
    u8 side;
    u8 i;

    if (battler >= gBattlersCount)
        return NULL;

    species = GetBattlerVisualSpecies(battler);
    side = GetBattlerSide(battler);

    for (i = 0; i < ARRAY_COUNT(sProfiles); i++)
    {
        if (sProfiles[i].species == species && sProfiles[i].side == side)
            return &sProfiles[i];
    }
    return NULL;
}

static void ClearAmbient(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;

    PmdGbaRuntime_Unbind(battler);
    sAmbient[battler].profile = NULL;
    sAmbient[battler].initialized = FALSE;
    sAmbient[battler].spriteId = SPRITE_NONE;
    sAmbient[battler].sequenceIndex = 0;
    sAmbient[battler].phase = PMD_AMBIENT_HOME;
    sAmbient[battler].homeTicksLeft = 0;
}

static void BindHome(u8 battler, const struct PmdSpeciesProfile *profile, u16 holdTicks, bool32 restartSequence)
{
    struct PmdAmbientState *state = &sAmbient[battler];

    if (profile == NULL || profile->home == NULL)
    {
        ClearAmbient(battler);
        return;
    }

    if (restartSequence)
        state->sequenceIndex = 0;

    if (!PmdGbaRuntime_Bind(battler, profile->home))
    {
        ClearAmbient(battler);
        return;
    }

    state->profile = profile;
    state->initialized = TRUE;
    state->spriteId = gBattlerSpriteIds[battler];
    state->phase = PMD_AMBIENT_HOME;
    state->homeTicksLeft = holdTicks;
}

static void BindCurrentAmbientAction(u8 battler, const struct PmdSpeciesProfile *profile)
{
    struct PmdAmbientState *state = &sAmbient[battler];
    const struct PmdGbaAction *action;

    if (profile == NULL)
    {
        ClearAmbient(battler);
        return;
    }

    action = profile->actions[state->sequenceIndex % PMD_G3R5_ACTION_COUNT];
    if (!PmdGbaRuntime_Bind(battler, action))
    {
        BindHome(battler, profile, 28, TRUE);
        return;
    }
    state->phase = PMD_AMBIENT_ACTION;
}

static const struct PmdGbaFrame *GetHomeFrame(const struct PmdSpeciesProfile *profile)
{
    if (profile == NULL || profile->home == NULL || profile->home->frames == NULL || profile->home->frameCount == 0)
        return NULL;
    return &profile->home->frames[0];
}

void PmdSoulGoldPrototype_PrimeLoadedBattlerBody(u8 battler)
{
    const struct PmdSpeciesProfile *profile = FindProfile(battler);
    const struct PmdGbaFrame *frame = GetHomeFrame(profile);
    if (frame != NULL)
        PmdSoulGold_PrimeLoadedBody(battler, frame);
}

void PmdSoulGoldPrototype_PrimeTemplateBody(u8 battler, u16 species)
{
    const struct PmdSpeciesProfile *profile = FindProfile(battler);
    const struct PmdGbaFrame *frame;

    if (profile == NULL || profile->species != species)
        return;
    frame = GetHomeFrame(profile);
    if (frame != NULL)
        PmdSoulGold_PrimeTemplateBody(battler, frame);
}

void PmdSoulGoldPrototype_PrimeCreatedSpriteBody(u8 battler, u16 species)
{
    const struct PmdSpeciesProfile *profile = FindProfile(battler);
    const struct PmdGbaFrame *frame;

    if (profile == NULL || profile->species != species)
        return;
    frame = GetHomeFrame(profile);
    if (frame != NULL)
        PmdSoulGold_PrimeCreatedSpriteBody(battler, frame);
}

void PmdSoulGoldPrototype_Init(void)
{
    u8 battler;

    PmdSoulGold_Init();
    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        sAmbient[battler].profile = NULL;
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
        struct PmdAmbientState *state = &sAmbient[battler];
        const struct PmdSpeciesProfile *profile;
        u8 spriteId;

        if (battler >= gBattlersCount)
        {
            PmdSoulGold_UpdateGroundShadow(battler, FALSE);
            ClearAmbient(battler);
            continue;
        }

        profile = FindProfile(battler);
        if (profile == NULL)
        {
            /* A PMD battler may have switched/transformed away. Remove our
             * owned shadow and restore SoulGold's native shadow callback. */
            PmdSoulGold_UpdateGroundShadow(battler, FALSE);
            ClearAmbient(battler);
            continue;
        }

        /* Ground shadow ownership is independent from body presentation. The
         * PMD-authored mask follows base x/y only, so move-animation x2/y2 and
         * G3R5 presentationY corrections never drag the ground layer around. */
        PmdSoulGold_UpdateGroundShadow(battler, TRUE);

        spriteId = gBattlerSpriteIds[battler];
        if (state->initialized && (state->spriteId != spriteId || state->profile != profile))
        {
            ClearAmbient(battler);
            state = &sAmbient[battler];
        }

        if (PmdGbaRuntime_ConsumeInterrupted(battler))
        {
            BindHome(battler, profile, 28, TRUE);
            continue;
        }

        if (!state->initialized)
        {
            BindHome(battler, profile, 28, TRUE);
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
            BindCurrentAmbientAction(battler, profile);
            continue;
        }

        if (state->phase == PMD_AMBIENT_ACTION && PmdGbaRuntime_IsComplete(battler))
        {
            u8 completedIndex = state->sequenceIndex % PMD_G3R5_ACTION_COUNT;
            state->sequenceIndex = (state->sequenceIndex + 1) % PMD_G3R5_ACTION_COUNT;
            BindHome(battler, profile, profile->homeHolds[completedIndex], FALSE);
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
