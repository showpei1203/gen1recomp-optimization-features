#include "global.h"
#include "battle.h"
#include "battle_controllers.h"
#include "battle_util.h"
#include "pokeball.h"
#include "sprite.h"
#include "constants/species.h"
#include "pmd_gba_runtime.h"
#include "pmd_soulgold_adapter.h"
#include "pmd_soulgold_dynamic_shadow.h"
#include "pmd_soulgold_prototype.h"

extern const struct PmdGbaAction gPmdCyndaquilPlayerHomeAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerIdleAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerWalkAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerNodAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerRotateAction;
extern const struct PmdGbaAction gPmdCyndaquilPlayerHurtAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerHomeShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerIdleShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerWalkShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerNodShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerRotateShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerHurtShadowAction;

extern const struct PmdGbaAction gPmdMarillOpponentHomeAction;
extern const struct PmdGbaAction gPmdMarillOpponentIdleAction;
extern const struct PmdGbaAction gPmdMarillOpponentWalkAction;
extern const struct PmdGbaAction gPmdMarillOpponentNodAction;
extern const struct PmdGbaAction gPmdMarillOpponentRotateAction;
extern const struct PmdGbaAction gPmdMarillOpponentHurtAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentHomeShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentIdleShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentWalkShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentNodShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentRotateShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentHurtShadowAction;

enum PmdPresentationPhase
{
    PMD_PHASE_HOME,
    PMD_PHASE_AMBIENT,
    PMD_PHASE_HURT,
    PMD_PHASE_HURT_RETURN,
};

#define PMD_G3R6A_AMBIENT_COUNT 4

struct PmdSpeciesProfile
{
    u16 species;
    u8 side;
    const struct PmdGbaAction *home;
    const struct PmdGbaAction *ambient[PMD_G3R6A_AMBIENT_COUNT];
    const struct PmdGbaAction *hurt;
    const struct PmdSoulGoldShadowAction *shadowHome;
    const struct PmdSoulGoldShadowAction *shadowAmbient[PMD_G3R6A_AMBIENT_COUNT];
    const struct PmdSoulGoldShadowAction *shadowHurt;
    u16 homeHolds[PMD_G3R6A_AMBIENT_COUNT];
};

struct PmdPresentationState
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
        .ambient =
        {
            &gPmdCyndaquilPlayerIdleAction,
            &gPmdCyndaquilPlayerWalkAction,
            &gPmdCyndaquilPlayerNodAction,
            &gPmdCyndaquilPlayerRotateAction,
        },
        .hurt = &gPmdCyndaquilPlayerHurtAction,
        .shadowHome = &gPmdCyndaquilPlayerHomeShadowAction,
        .shadowAmbient =
        {
            &gPmdCyndaquilPlayerIdleShadowAction,
            &gPmdCyndaquilPlayerWalkShadowAction,
            &gPmdCyndaquilPlayerNodShadowAction,
            &gPmdCyndaquilPlayerRotateShadowAction,
        },
        .shadowHurt = &gPmdCyndaquilPlayerHurtShadowAction,
        .homeHolds = {28, 18, 24, 24},
    },
    {
        .species = SPECIES_MARILL,
        .side = B_SIDE_OPPONENT,
        .home = &gPmdMarillOpponentHomeAction,
        .ambient =
        {
            &gPmdMarillOpponentIdleAction,
            &gPmdMarillOpponentWalkAction,
            &gPmdMarillOpponentNodAction,
            &gPmdMarillOpponentRotateAction,
        },
        .hurt = &gPmdMarillOpponentHurtAction,
        .shadowHome = &gPmdMarillOpponentHomeShadowAction,
        .shadowAmbient =
        {
            &gPmdMarillOpponentIdleShadowAction,
            &gPmdMarillOpponentWalkShadowAction,
            &gPmdMarillOpponentNodShadowAction,
            &gPmdMarillOpponentRotateShadowAction,
        },
        .shadowHurt = &gPmdMarillOpponentHurtShadowAction,
        .homeHolds = {26, 18, 22, 24},
    },
};

static struct PmdPresentationState sState[PMD_GBA_MAX_BATTLERS];

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

static void ClearState(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;
    PmdSoulGold_SetReactivePresentation(battler, FALSE);
    PmdGbaRuntime_Unbind(battler);
    sState[battler].profile = NULL;
    sState[battler].initialized = FALSE;
    sState[battler].spriteId = SPRITE_NONE;
    sState[battler].sequenceIndex = 0;
    sState[battler].phase = PMD_PHASE_HOME;
    sState[battler].homeTicksLeft = 0;
}

static void BindHome(u8 battler, const struct PmdSpeciesProfile *profile, u16 holdTicks, bool32 restartSequence)
{
    struct PmdPresentationState *state = &sState[battler];

    if (profile == NULL || profile->home == NULL)
    {
        ClearState(battler);
        return;
    }
    if (restartSequence)
        state->sequenceIndex = 0;
    if (!PmdGbaRuntime_Bind(battler, profile->home))
    {
        ClearState(battler);
        return;
    }
    state->profile = profile;
    state->initialized = TRUE;
    state->spriteId = gBattlerSpriteIds[battler];
    state->phase = PMD_PHASE_HOME;
    state->homeTicksLeft = holdTicks;
}

static void BindCurrentAmbient(u8 battler, const struct PmdSpeciesProfile *profile)
{
    struct PmdPresentationState *state = &sState[battler];
    const struct PmdGbaAction *action;

    if (profile == NULL)
    {
        ClearState(battler);
        return;
    }
    action = profile->ambient[state->sequenceIndex % PMD_G3R6A_AMBIENT_COUNT];
    if (!PmdGbaRuntime_Bind(battler, action))
    {
        BindHome(battler, profile, 28, TRUE);
        return;
    }
    state->phase = PMD_PHASE_AMBIENT;
}

static bool32 BindHurt(u8 battler, const struct PmdSpeciesProfile *profile)
{
    struct PmdPresentationState *state = &sState[battler];

    if (profile == NULL || profile->hurt == NULL)
        return FALSE;
    PmdSoulGold_SetReactivePresentation(battler, TRUE);
    if (!PmdGbaRuntime_Bind(battler, profile->hurt))
    {
        PmdSoulGold_SetReactivePresentation(battler, FALSE);
        return FALSE;
    }
    state->profile = profile;
    state->initialized = TRUE;
    state->spriteId = gBattlerSpriteIds[battler];
    state->phase = PMD_PHASE_HURT;
    state->homeTicksLeft = 0;
    return TRUE;
}

static const struct PmdGbaFrame *GetHomeFrame(const struct PmdSpeciesProfile *profile)
{
    if (profile == NULL || profile->home == NULL || profile->home->frames == NULL || profile->home->frameCount == 0)
        return NULL;
    return &profile->home->frames[0];
}

static const struct PmdSoulGoldShadowAction *GetCurrentShadowAction(const struct PmdPresentationState *state)
{
    if (state == NULL || state->profile == NULL)
        return NULL;
    if (state->phase == PMD_PHASE_HURT)
        return state->profile->shadowHurt;
    if (state->phase == PMD_PHASE_HOME || state->phase == PMD_PHASE_HURT_RETURN)
        return state->profile->shadowHome;
    return state->profile->shadowAmbient[state->sequenceIndex % PMD_G3R6A_AMBIENT_COUNT];
}

static void CompletePmdHurt(enum BattlerId battler)
{
    PmdSoulGold_SetReactivePresentation(battler, FALSE);
    gDoingBattleAnim = FALSE;
    BtlController_Complete(battler);
}

static void WaitForPmdHurt(enum BattlerId battler)
{
    struct PmdPresentationState *state;
    const struct PmdSpeciesProfile *profile;

    if (battler >= PMD_GBA_MAX_BATTLERS)
    {
        gDoingBattleAnim = FALSE;
        BtlController_Complete(battler);
        return;
    }
    state = &sState[battler];
    profile = FindProfile(battler);
    if (profile == NULL || state->profile != profile)
    {
        CompletePmdHurt(battler);
        return;
    }

    if (state->phase == PMD_PHASE_HURT)
    {
        if (!PmdGbaRuntime_IsComplete(battler))
            return;
        BindHome(battler, profile, 28, TRUE);
        state->phase = PMD_PHASE_HURT_RETURN;
        return;
    }

    if (state->phase == PMD_PHASE_HURT_RETURN)
    {
        /* Keep reactive ownership and SoulGold's battle-animation busy flag
         * until HOME has actually replaced the last Hurt frame in OBJ VRAM. */
        if (!PmdGbaRuntime_IsPresenting(battler))
            return;
        state->phase = PMD_PHASE_HOME;
        CompletePmdHurt(battler);
        return;
    }

    CompletePmdHurt(battler);
}

void PmdSoulGoldPrototype_HandleHitAnimation(enum BattlerId battler)
{
    const struct PmdSpeciesProfile *profile = FindProfile(battler);
    u8 spriteId = gBattlerSpriteIds[battler];

    if (profile == NULL || spriteId >= MAX_SPRITES || gSprites[spriteId].invisible)
    {
        BtlController_HandleHitAnimation(battler);
        return;
    }

    /* CONTROLLER_HITANIMATION is the semantic trigger for PMDCollab Hurt.
     * Preserve native command busy-state and healthbox feedback, replacing only
     * the native body blink/shake visual for PMD-profiled battlers. */
    if (!BindHurt(battler, profile))
    {
        BtlController_HandleHitAnimation(battler);
        return;
    }
    gDoingBattleAnim = TRUE;
    gSprites[spriteId].data[1] = 0;
    DoHitAnimHealthboxEffect(battler);
    gBattlerControllerFuncs[battler] = WaitForPmdHurt;
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
    PmdSoulGoldDynamicShadow_Init();
    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        sState[battler].profile = NULL;
        sState[battler].initialized = FALSE;
        sState[battler].spriteId = SPRITE_NONE;
        sState[battler].sequenceIndex = 0;
        sState[battler].phase = PMD_PHASE_HOME;
        sState[battler].homeTicksLeft = 0;
    }
}

void PmdSoulGoldPrototype_Tick(void)
{
    u8 battler;

    PmdGbaRuntime_Tick();

    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        struct PmdPresentationState *state = &sState[battler];
        const struct PmdSpeciesProfile *profile;
        const struct PmdSoulGoldShadowAction *shadowAction;
        u8 spriteId;

        if (battler >= gBattlersCount)
        {
            PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);
            ClearState(battler);
            continue;
        }

        profile = FindProfile(battler);
        if (profile == NULL)
        {
            PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);
            ClearState(battler);
            continue;
        }

        spriteId = gBattlerSpriteIds[battler];
        if (state->initialized && (state->spriteId != spriteId || state->profile != profile))
        {
            PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);
            ClearState(battler);
            state = &sState[battler];
        }

        if (PmdGbaRuntime_ConsumeInterrupted(battler))
        {
            /* Reactive Hurt owns its controller command. If it loses PMD
             * presentation ownership, abandon the stale reaction and return
             * HOME; WaitForPmdHurt will release the controller safely. */
            if (state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN)
                PmdSoulGold_SetReactivePresentation(battler, FALSE);
            PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);
            BindHome(battler, profile, 28, TRUE);
            continue;
        }

        if (!state->initialized)
        {
            PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);
            BindHome(battler, profile, 28, TRUE);
            continue;
        }

        shadowAction = GetCurrentShadowAction(state);
        PmdSoulGoldDynamicShadow_Update(
            battler,
            PmdGbaRuntime_IsPresenting(battler),
            shadowAction,
            PmdGbaRuntime_GetFrameIndex(battler));

        if (state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN)
            continue;

        if (state->phase == PMD_PHASE_HOME)
        {
            if (!PmdGbaRuntime_IsPresenting(battler))
                continue;
            if (state->homeTicksLeft > 0)
            {
                state->homeTicksLeft--;
                continue;
            }
            BindCurrentAmbient(battler, profile);
            continue;
        }

        if (state->phase == PMD_PHASE_AMBIENT && PmdGbaRuntime_IsComplete(battler))
        {
            u8 completedIndex = state->sequenceIndex % PMD_G3R6A_AMBIENT_COUNT;
            state->sequenceIndex = (state->sequenceIndex + 1) % PMD_G3R6A_AMBIENT_COUNT;
            BindHome(battler, profile, profile->homeHolds[completedIndex], FALSE);
        }
    }
}

void PmdSoulGoldPrototype_Reset(void)
{
    u8 battler;

    PmdSoulGoldDynamicShadow_Reset();
    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
        ClearState(battler);
    PmdSoulGold_Reset();
}
