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

static void ClearBinding(u8 battler)
{
    if (battler >= SHOWDOWN_GBA_MAX_BATTLERS)
        return;
    if (sBound[battler])
        ShowdownGbaRuntime_Unbind(battler);
    sBound[battler] = FALSE;
    sBoundSpriteId[battler] = SPRITE_NONE;
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

void ShowdownSoulGoldPrototype_Tick(void)
{
    u8 battler;

    for (battler = 0; battler < SHOWDOWN_GBA_MAX_BATTLERS; battler++)
    {
        const struct ShowdownGbaAction *action = NULL;
        u16 species;
        u8 spriteId;

        if (battler >= gBattlersCount)
        {
            ClearBinding(battler);
            continue;
        }

        species = GetBattlerVisualSpecies(battler);
        spriteId = gBattlerSpriteIds[battler];

        if (GetBattlerSide(battler) == B_SIDE_PLAYER && species == SPECIES_SPRIGATITO)
            action = &gShowdownSprigatitoBackIdleAction;
        else if (GetBattlerSide(battler) == B_SIDE_OPPONENT && species == SPECIES_MARILL)
            action = &gShowdownMarillFrontIdleAction;

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
