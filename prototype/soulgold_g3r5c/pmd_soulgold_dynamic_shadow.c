#include "global.h"
#include "battle.h"
#include "battle_gfx_sfx_util.h"
#include "battle_interface.h"
#include "pokemon.h"
#include "sprite.h"
#include "constants/species.h"
#include "pmd_soulgold_dynamic_shadow.h"

/*
 * G3R5C shadow ownership.
 *
 * PMDCollab's format defines *-Shadow.png per animation frame. White is the
 * official shadow position; the colored components define the shadow mask.
 * G3R5/G3R5B incorrectly collapsed that timeline to Idle0. This module keeps
 * a separate shadow OBJ but advances its tile and authored offset in lockstep
 * with the PMD body frame.
 *
 * Battle calibration rule:
 * - Idle0 X is centered on SoulGold battler base X (accepted runtime fix).
 * - Per-frame PMD shadow deltas from Idle0 are preserved.
 * - Body x2/y2 is included, so any PMD presentation translation moves the
 *   shadow with the body instead of leaving it nailed to the battlefield.
 */

extern const u8 gPmdCyndaquilPlayerGroundShadowGfx[];
extern const u16 gPmdCyndaquilPlayerGroundShadowGfxSize;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerHomeShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerIdleShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerWalkShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerNodShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerRotateShadowAction;

extern const u8 gPmdMarillOpponentGroundShadowGfx[];
extern const u16 gPmdMarillOpponentGroundShadowGfxSize;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentHomeShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentIdleShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentWalkShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentNodShadowAction;
extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentRotateShadowAction;

#define TAG_PMD_CYNDAQUIL_DYNAMIC_SHADOW_TILE 0xF3D7
#define TAG_PMD_MARILL_DYNAMIC_SHADOW_TILE    0xF3D8

static u8 sShadowSpriteIds[4];
static bool8 sNativeShadowSuppressed[4];

static const struct OamData sDynamicShadowOam =
{
    .y = 0,
    .affineMode = ST_OAM_AFFINE_OFF,
    .objMode = ST_OAM_OBJ_NORMAL,
    .mosaic = FALSE,
    .bpp = ST_OAM_4BPP,
    .shape = SPRITE_SHAPE(32x8),
    .x = 0,
    .matrixNum = 0,
    .size = SPRITE_SIZE(32x8),
    .tileNum = 0,
    .priority = 3,
    .paletteNum = 0,
    .affineParam = 0,
};

static const union AnimCmd sDynamicShadowAnim[] =
{
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_END,
};

static const union AnimCmd *const sDynamicShadowAnims[] =
{
    sDynamicShadowAnim,
};

static const struct SpriteTemplate sCyndaquilDynamicShadowTemplate =
{
    .tileTag = TAG_PMD_CYNDAQUIL_DYNAMIC_SHADOW_TILE,
    .paletteTag = TAG_SHADOW_PAL,
    .oam = &sDynamicShadowOam,
    .anims = sDynamicShadowAnims,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};

static const struct SpriteTemplate sMarillDynamicShadowTemplate =
{
    .tileTag = TAG_PMD_MARILL_DYNAMIC_SHADOW_TILE,
    .paletteTag = TAG_SHADOW_PAL,
    .oam = &sDynamicShadowOam,
    .anims = sDynamicShadowAnims,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};

struct PmdDynamicShadowProfile
{
    u16 species;
    u8 side;
    const u8 *gfx;
    const u16 *gfxSize;
    u16 tileTag;
    const struct SpriteTemplate *template;
};

static const struct PmdDynamicShadowProfile sProfiles[] =
{
    {
        .species = SPECIES_CYNDAQUIL,
        .side = B_SIDE_PLAYER,
        .gfx = gPmdCyndaquilPlayerGroundShadowGfx,
        .gfxSize = &gPmdCyndaquilPlayerGroundShadowGfxSize,
        .tileTag = TAG_PMD_CYNDAQUIL_DYNAMIC_SHADOW_TILE,
        .template = &sCyndaquilDynamicShadowTemplate,
    },
    {
        .species = SPECIES_MARILL,
        .side = B_SIDE_OPPONENT,
        .gfx = gPmdMarillOpponentGroundShadowGfx,
        .gfxSize = &gPmdMarillOpponentGroundShadowGfxSize,
        .tileTag = TAG_PMD_MARILL_DYNAMIC_SHADOW_TILE,
        .template = &sMarillDynamicShadowTemplate,
    },
};

static const struct PmdDynamicShadowProfile *FindProfile(u8 battler)
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

static bool32 SuppressNativeShadow(u8 battler)
{
    bool32 suppressed = FALSE;
    u8 spriteId;

    if (gBattleSpritesDataPtr == NULL || battler >= gBattlersCount)
        return FALSE;

    spriteId = gBattleSpritesDataPtr->healthBoxesData[battler].shadowSpriteIdPrimary;
    if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
    {
        gSprites[spriteId].callback = SpriteCallbackDummy;
        gSprites[spriteId].invisible = TRUE;
        suppressed = TRUE;
    }

    if (B_ENEMY_MON_SHADOW_STYLE >= GEN_4 && P_GBA_STYLE_SPECIES_GFX == FALSE)
    {
        spriteId = gBattleSpritesDataPtr->healthBoxesData[battler].shadowSpriteIdSecondary;
        if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
        {
            gSprites[spriteId].callback = SpriteCallbackDummy;
            gSprites[spriteId].invisible = TRUE;
            suppressed = TRUE;
        }
    }

    if (suppressed && battler < ARRAY_COUNT(sNativeShadowSuppressed))
        sNativeShadowSuppressed[battler] = TRUE;
    return suppressed;
}

static void RestoreNativeShadow(u8 battler)
{
    if (battler >= ARRAY_COUNT(sNativeShadowSuppressed) || !sNativeShadowSuppressed[battler])
        return;
    if (gBattleSpritesDataPtr != NULL && battler < gBattlersCount)
        SetBattlerShadowSpriteCallback(battler, GetBattlerVisualSpecies(battler));
    sNativeShadowSuppressed[battler] = FALSE;
}

static void HideOwnedShadow(u8 battler)
{
    u8 spriteId;

    if (battler >= ARRAY_COUNT(sShadowSpriteIds))
        return;
    spriteId = sShadowSpriteIds[battler];
    if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
        gSprites[spriteId].invisible = TRUE;
}

void PmdSoulGoldDynamicShadow_Init(void)
{
    u8 i;

    for (i = 0; i < ARRAY_COUNT(sProfiles); i++)
    {
        struct SpriteSheet sheet =
        {
            .data = sProfiles[i].gfx,
            .size = *sProfiles[i].gfxSize,
            .tag = sProfiles[i].tileTag,
        };
        LoadSpriteSheet(&sheet);
    }

    for (i = 0; i < ARRAY_COUNT(sShadowSpriteIds); i++)
    {
        sShadowSpriteIds[i] = SPRITE_NONE;
        sNativeShadowSuppressed[i] = FALSE;
    }
}

void PmdSoulGoldDynamicShadow_Reset(void)
{
    u8 battler;

    for (battler = 0; battler < ARRAY_COUNT(sShadowSpriteIds); battler++)
    {
        u8 spriteId = sShadowSpriteIds[battler];
        if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
            DestroySprite(&gSprites[spriteId]);
        sShadowSpriteIds[battler] = SPRITE_NONE;
        RestoreNativeShadow(battler);
    }
}

void PmdSoulGoldDynamicShadow_Update(
    u8 battler,
    bool32 active,
    const struct PmdSoulGoldShadowAction *action,
    u8 frameIndex)
{
    const struct PmdDynamicShadowProfile *profile;
    const struct PmdSoulGoldShadowFrame *frame;
    u8 bodySpriteId;
    u8 shadowSpriteId;
    u16 tileStart;
    struct Sprite *body;
    struct Sprite *shadow;

    if (battler >= ARRAY_COUNT(sShadowSpriteIds))
        return;

    profile = active ? FindProfile(battler) : NULL;
    if (!active || profile == NULL || action == NULL || frameIndex >= action->frameCount)
    {
        HideOwnedShadow(battler);
        RestoreNativeShadow(battler);
        return;
    }

    bodySpriteId = gBattlerSpriteIds[battler];
    if (bodySpriteId >= MAX_SPRITES || !gSprites[bodySpriteId].inUse)
    {
        HideOwnedShadow(battler);
        RestoreNativeShadow(battler);
        return;
    }
    body = &gSprites[bodySpriteId];

    tileStart = GetSpriteTileStartByTag(profile->tileTag);
    if (tileStart == 0xFFFF)
    {
        HideOwnedShadow(battler);
        RestoreNativeShadow(battler);
        return;
    }

    SuppressNativeShadow(battler);
    shadowSpriteId = sShadowSpriteIds[battler];
    if (shadowSpriteId >= MAX_SPRITES || !gSprites[shadowSpriteId].inUse)
    {
        shadowSpriteId = CreateSprite(profile->template, body->x, body->y, 0xC8);
        if (shadowSpriteId >= MAX_SPRITES)
        {
            sShadowSpriteIds[battler] = SPRITE_NONE;
            RestoreNativeShadow(battler);
            return;
        }
        sShadowSpriteIds[battler] = shadowSpriteId;
    }

    frame = &action->frames[frameIndex];
    shadow = &gSprites[shadowSpriteId];
    shadow->callback = SpriteCallbackDummy;
    shadow->oam.tileNum = tileStart + frame->tileOffset;

    /*
     * This is the key G3R5C relation. Shadow metadata supplies the authored
     * per-frame offset, while body x2/y2 supplies the actual PMD presentation
     * translation. Consequently a left/right step, vertical move, jump, or a
     * 1px body correction moves the shadow in the same rendered coordinate
     * system instead of leaving it behind.
     */
    shadow->x = body->x + body->x2 + frame->xOffset;
    shadow->y = body->y + body->y2 + frame->yOffset;
    shadow->x2 = 0;
    shadow->y2 = 0;
    shadow->invisible = body->invisible;
}
