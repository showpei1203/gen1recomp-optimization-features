#include "global.h"
#include "battle.h"
#include "battle_util.h"
#include "sprite.h"
#include "constants/species.h"
#include "showdown_gba_runtime.h"
#include "showdown_soulgold_adapter.h"
#include "showdown_soulgold_prototype.h"

extern const struct ShowdownGbaAction gShowdownSprigatitoBackIdleAction;
extern const struct ShowdownGbaAction gShowdownMarillFrontIdleAction;

static bool8 sBound[SHOWDOWN_GBA_MAX_BATTLERS];
static u8 sBoundSpriteId[SHOWDOWN_GBA_MAX_BATTLERS];

static const struct ShowdownGbaAction *FindActionForSpeciesSide(u16 species, u8 side)
{
    if (side == B_SIDE_PLAYER && species == SPECIES_SPRIGATITO)
        return &gShowdownSprigatitoBackIdleAction;
    if (side == B_SIDE_OPPONENT && species == SPECIES_MARILL)
        return &gShowdownMarillFrontIdleAction;
    return NULL;
}

static const struct ShowdownGbaAction *FindActionForBattler(u8 battler)
{
    if (battler >= gBattlersCount)
        return NULL;
    return FindActionForSpeciesSide(GetBattlerVisualSpecies(battler), GetBattlerSide(battler));
}

static const struct ShowdownGbaFrame *GetFirstFrame(const struct ShowdownGbaAction *action)
{
    if (action == NULL || action->frames == NULL || action->frameCount == 0)
        return NULL;
    return &action->frames[0];
}

static void ClearBinding(u8 battler)
{
    if (battler >= SHOWDOWN_GBA_MAX_BATTLERS)
        return;
    if (sBound[battler])
        ShowdownGbaRuntime_Unbind(battler);
    sBound[battler] = FALSE;
    sBoundSpriteId[battler] = SPRITE_NONE;
}

void ShowdownSoulGoldPrototype_PrimeLoadedBattlerBody(u8 battler)
{
    const struct ShowdownGbaAction *action = FindActionForBattler(battler);
    const struct ShowdownGbaFrame *frame = GetFirstFrame(action);

    if (frame != NULL)
        ShowdownSoulGold_PrimeLoadedBody(battler, frame);
}

void ShowdownSoulGoldPrototype_PrimeTemplateBody(u8 battler, u16 species)
{
    const struct ShowdownGbaAction *action;
    const struct ShowdownGbaFrame *frame;

    if (battler >= gBattlersCount)
        return;

    action = FindActionForSpeciesSide(species, GetBattlerSide(battler));
    frame = GetFirstFrame(action);
    if (frame != NULL)
        ShowdownSoulGold_PrimeTemplateBody(battler, frame);
}

void ShowdownSoulGoldPrototype_PrimeCreatedSpriteBody(u8 battler, u16 species)
{
    const struct ShowdownGbaAction *action;
    const struct ShowdownGbaFrame *frame;

    if (battler >= gBattlersCount)
        return;

    action = FindActionForSpeciesSide(species, GetBattlerSide(battler));
    frame = GetFirstFrame(action);
    if (frame != NULL)
        ShowdownSoulGold_PrimeCreatedSpriteBody(battler, frame);
}

void ShowdownSoulGoldPrototype_Init(void)
{
    u8 battler;

    ShowdownSoulGold_Init();
    for (battler = 0; battler < SHOWDOWN_GBA_MAX_BATTLERS; battler++)
    {
        sBound[battler] = FALSE;
        sBoundSpriteId[battler] = SPRITE_NONE;
    }
}

void ShowdownSoulGoldPrototype_PrepareOam(void)
{
    u8 battler;

    for (battler = 0; battler < SHOWDOWN_GBA_MAX_BATTLERS; battler++)
    {
        if (battler < gBattlersCount && FindActionForBattler(battler) != NULL)
            ShowdownSoulGold_PrepareOam(battler);
    }
}

void ShowdownSoulGoldPrototype_Tick(void)
{
    u8 battler;

    for (battler = 0; battler < SHOWDOWN_GBA_MAX_BATTLERS; battler++)
    {
        const struct ShowdownGbaAction *action;
        u8 spriteId;

        if (battler >= gBattlersCount)
        {
            ClearBinding(battler);
            continue;
        }

        action = FindActionForBattler(battler);
        spriteId = gBattlerSpriteIds[battler];

        if (action == NULL)
        {
            ClearBinding(battler);
            continue;
        }

        if (sBound[battler] && sBoundSpriteId[battler] != spriteId)
            ClearBinding(battler);

        if (!sBound[battler])
        {
            if (ShowdownGbaRuntime_Bind(battler, action))
            {
                sBound[battler] = TRUE;
                sBoundSpriteId[battler] = spriteId;
            }
        }
    }

    ShowdownGbaRuntime_Tick();
}

void ShowdownSoulGoldPrototype_Reset(void)
{
    u8 battler;

    for (battler = 0; battler < SHOWDOWN_GBA_MAX_BATTLERS; battler++)
        ClearBinding(battler);
    ShowdownSoulGold_Reset();
}
