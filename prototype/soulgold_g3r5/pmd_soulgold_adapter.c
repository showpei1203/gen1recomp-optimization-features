#include "global.h"
#include "battle.h"
#include "battle_gfx_sfx_util.h"
#include "battle_interface.h"
#include "battle_main.h"
#include "data.h"
#include "decompress.h"
#include "pokemon.h"
#include "sprite.h"
#include "constants/species.h"
#include "pmd_gba_runtime.h"
#include "pmd_soulgold_adapter.h"

/*
 * G3R5 ground shadows are generated directly from PMDCollab Idle-Shadow.png
 * metadata at the pinned SpriteCollab revision. The selected component mask is
 * packed to a compact 32x8 4bpp OBJ. Palette index 1 intentionally reuses
 * SoulGold's TAG_SHADOW_PAL so the visual remains compatible with the battle
 * palette while the geometry/placement comes from PMD authority.
 */
extern const u8 gPmdCyndaquilPlayerGroundShadowGfx[0x80];
extern const s8 gPmdCyndaquilPlayerGroundShadowXOffset;
extern const s8 gPmdCyndaquilPlayerGroundShadowYOffset;
extern const u8 gPmdCyndaquilPlayerGroundShadowShadowSize;

extern const u8 gPmdMarillOpponentGroundShadowGfx[0x80];
extern const s8 gPmdMarillOpponentGroundShadowXOffset;
extern const s8 gPmdMarillOpponentGroundShadowYOffset;
extern const u8 gPmdMarillOpponentGroundShadowShadowSize;

#define TAG_PMD_CYNDAQUIL_GROUND_SHADOW_TILE 0xF3D5
#define TAG_PMD_MARILL_GROUND_SHADOW_TILE    0xF3D6

static u8 sPmdGroundShadowSpriteIds[PMD_GBA_MAX_BATTLERS];
static bool8 sNativeShadowSuppressed[PMD_GBA_MAX_BATTLERS];

static const struct SpriteSheet sPmdGroundShadowSheets[] =
{
    {
        .data = gPmdCyndaquilPlayerGroundShadowGfx,
        .size = 0x80,
        .tag = TAG_PMD_CYNDAQUIL_GROUND_SHADOW_TILE,
    },
    {
        .data = gPmdMarillOpponentGroundShadowGfx,
        .size = 0x80,
        .tag = TAG_PMD_MARILL_GROUND_SHADOW_TILE,
    },
};

static const struct OamData sPmdGroundShadowOam =
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

static const union AnimCmd sPmdGroundShadowAnim[] =
{
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_END,
};

static const union AnimCmd *const sPmdGroundShadowAnims[] =
{
    sPmdGroundShadowAnim,
};

static const struct SpriteTemplate sPmdCyndaquilGroundShadowTemplate =
{
    .tileTag = TAG_PMD_CYNDAQUIL_GROUND_SHADOW_TILE,
    .paletteTag = TAG_SHADOW_PAL,
    .oam = &sPmdGroundShadowOam,
    .anims = sPmdGroundShadowAnims,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};

static const struct SpriteTemplate sPmdMarillGroundShadowTemplate =
{
    .tileTag = TAG_PMD_MARILL_GROUND_SHADOW_TILE,
    .paletteTag = TAG_SHADOW_PAL,
    .oam = &sPmdGroundShadowOam,
    .anims = sPmdGroundShadowAnims,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};

struct PmdGroundShadowProfile
{
    u16 species;
    u8 side;
    const struct SpriteTemplate *template;
    const s8 *xOffset;
    const s8 *yOffset;
    const u8 *shadowSize;
};

static const struct PmdGroundShadowProfile sPmdGroundShadowProfiles[] =
{
    {
        .species = SPECIES_CYNDAQUIL,
        .side = B_SIDE_PLAYER,
        .template = &sPmdCyndaquilGroundShadowTemplate,
        .xOffset = &gPmdCyndaquilPlayerGroundShadowXOffset,
        .yOffset = &gPmdCyndaquilPlayerGroundShadowYOffset,
        .shadowSize = &gPmdCyndaquilPlayerGroundShadowShadowSize,
    },
    {
        .species = SPECIES_MARILL,
        .side = B_SIDE_OPPONENT,
        .template = &sPmdMarillGroundShadowTemplate,
        .xOffset = &gPmdMarillOpponentGroundShadowXOffset,
        .yOffset = &gPmdMarillOpponentGroundShadowYOffset,
        .shadowSize = &gPmdMarillOpponentGroundShadowShadowSize,
    },
};

static const struct PmdGroundShadowProfile *sActiveShadowProfiles[PMD_GBA_MAX_BATTLERS];

static const struct PmdGroundShadowProfile *FindGroundShadowProfile(u8 battler)
{
    u16 species;
    u8 side;
    u8 i;

    if (battler >= gBattlersCount)
        return NULL;

    species = GetBattlerVisualSpecies(battler);
    side = GetBattlerSide(battler);
    for (i = 0; i < ARRAY_COUNT(sPmdGroundShadowProfiles); i++)
    {
        if (sPmdGroundShadowProfiles[i].species == species
         && sPmdGroundShadowProfiles[i].side == side)
            return &sPmdGroundShadowProfiles[i];
    }
    return NULL;
}

static bool32 SoulGold_CanPresentBattler(u8 battler)
{
    enum BattlerPosition position;
    u8 spriteId;
    struct Sprite *sprite;

    if (battler >= gBattlersCount)
        return FALSE;
    if (gMonSpritesGfxPtr == NULL || gBattleSpritesDataPtr == NULL)
        return FALSE;
    if (!InBattleChoosingMoves())
        return FALSE;

    spriteId = gBattlerSpriteIds[battler];
    if (spriteId >= MAX_SPRITES || !gSprites[spriteId].inUse || gSprites[spriteId].invisible)
        return FALSE;

    position = GetBattlerPosition(battler);
    sprite = &gSprites[spriteId];
    if (sprite->images != gMonSpritesGfxPtr->frameImages[position])
        return FALSE;

    if (gDoingBattleAnim)
        return FALSE;
    if (gBattleSpritesDataPtr->healthBoxesData[battler].animFromTableActive)
        return FALSE;
    if (gBattleSpritesDataPtr->healthBoxesData[battler].specialAnimActive)
        return FALSE;
    if (gBattleSpritesDataPtr->healthBoxesData[battler].statusAnimActive)
        return FALSE;

    return TRUE;
}

static bool32 SoulGold_StageFrame(u8 battler, u8 cacheSlot, const struct PmdGbaFrame *frame)
{
    enum BattlerPosition position;
    u8 *dest;

    if (frame == NULL || frame->gfx == NULL || cacheSlot >= PMD_GBA_CACHE_SLOTS)
        return FALSE;
    if (gMonSpritesGfxPtr == NULL || battler >= gBattlersCount)
        return FALSE;

    position = GetBattlerPosition(battler);
    dest = gMonSpritesGfxPtr->spritesGfx[position] + cacheSlot * MON_PIC_SIZE;
    DecompressDataWithHeaderWram(frame->gfx, dest);
    return TRUE;
}

static void SoulGold_PresentSlot(u8 battler, u8 cacheSlot)
{
    u8 spriteId = gBattlerSpriteIds[battler];
    struct Sprite *sprite;

    if (spriteId >= MAX_SPRITES || cacheSlot >= PMD_GBA_CACHE_SLOTS)
        return;

    sprite = &gSprites[spriteId];
    if (sprite->images == NULL)
        return;

    RequestSpriteFrameImageCopy(cacheSlot, sprite->oam.tileNum, sprite->images);
}

static void SoulGold_SetPresentationOffset(u8 battler, s16 x, s16 y)
{
    u8 spriteId = gBattlerSpriteIds[battler];

    if (spriteId >= MAX_SPRITES)
        return;
    gSprites[spriteId].x2 = x;
    gSprites[spriteId].y2 = y;
}

static const struct PmdGbaHostOps sSoulGoldPmdHostOps =
{
    .CanPresentBattler = SoulGold_CanPresentBattler,
    .StageFrame = SoulGold_StageFrame,
    .PresentSlot = SoulGold_PresentSlot,
    .SetPresentationOffset = SoulGold_SetPresentationOffset,
};

static bool32 PrimeImageArray(const struct SpriteFrameImage *images, const struct PmdGbaFrame *frame)
{
    u8 slot;

    if (images == NULL || frame == NULL || frame->gfx == NULL)
        return FALSE;

    for (slot = 0; slot < PMD_GBA_CACHE_SLOTS; slot++)
    {
        if (images[slot].data == NULL || images[slot].relativeFrames || images[slot].size < MON_PIC_SIZE)
            return FALSE;
    }

    for (slot = 0; slot < PMD_GBA_CACHE_SLOTS; slot++)
        DecompressDataWithHeaderWram(frame->gfx, (void *)images[slot].data);

    return TRUE;
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

    /* Match SoulGold's native two-shadow condition before touching Secondary.
     * In the single-shadow path this field is not initialized as an active id. */
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

    if (suppressed)
        sNativeShadowSuppressed[battler] = TRUE;
    return suppressed;
}

static void RestoreNativeShadow(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS || !sNativeShadowSuppressed[battler])
        return;

    if (gBattleSpritesDataPtr != NULL && battler < gBattlersCount)
        SetBattlerShadowSpriteCallback(battler, GetBattlerVisualSpecies(battler));
    sNativeShadowSuppressed[battler] = FALSE;
}

static void HideOwnedShadow(u8 battler)
{
    u8 shadowSpriteId;

    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;
    shadowSpriteId = sPmdGroundShadowSpriteIds[battler];
    if (shadowSpriteId < MAX_SPRITES && gSprites[shadowSpriteId].inUse)
        gSprites[shadowSpriteId].invisible = TRUE;
}

void PmdSoulGold_UpdateGroundShadow(u8 battler, bool32 active)
{
    const struct PmdGroundShadowProfile *profile;
    u8 bodySpriteId;
    u8 shadowSpriteId;
    struct Sprite *body;
    struct Sprite *shadow;

    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;

    profile = active ? FindGroundShadowProfile(battler) : NULL;
    if (!active || profile == NULL || battler >= gBattlersCount)
    {
        HideOwnedShadow(battler);
        sActiveShadowProfiles[battler] = NULL;
        RestoreNativeShadow(battler);
        return;
    }

    SuppressNativeShadow(battler);

    bodySpriteId = gBattlerSpriteIds[battler];
    if (bodySpriteId >= MAX_SPRITES || !gSprites[bodySpriteId].inUse)
    {
        HideOwnedShadow(battler);
        return;
    }
    body = &gSprites[bodySpriteId];

    shadowSpriteId = sPmdGroundShadowSpriteIds[battler];
    if (sActiveShadowProfiles[battler] != profile)
    {
        if (shadowSpriteId < MAX_SPRITES && gSprites[shadowSpriteId].inUse)
            DestroySprite(&gSprites[shadowSpriteId]);
        shadowSpriteId = SPRITE_NONE;
        sPmdGroundShadowSpriteIds[battler] = SPRITE_NONE;
        sActiveShadowProfiles[battler] = profile;
    }

    if (shadowSpriteId >= MAX_SPRITES || !gSprites[shadowSpriteId].inUse)
    {
        shadowSpriteId = CreateSprite(
            profile->template,
            body->x + *profile->xOffset,
            body->y + *profile->yOffset,
            0xC8);
        if (shadowSpriteId >= MAX_SPRITES)
        {
            sPmdGroundShadowSpriteIds[battler] = SPRITE_NONE;
            return;
        }
        sPmdGroundShadowSpriteIds[battler] = shadowSpriteId;
    }

    shadow = &gSprites[shadowSpriteId];
    shadow->callback = SpriteCallbackDummy;
    /* Ground ownership uses base x/y only. PMD presentation x2/y2 may correct
     * body frames but must never drag the shadow off the battlefield ground. */
    shadow->x = body->x + *profile->xOffset;
    shadow->y = body->y + *profile->yOffset;
    shadow->x2 = 0;
    shadow->y2 = 0;
    shadow->invisible = body->invisible;
}

bool32 PmdSoulGold_PrimeLoadedBody(u8 battler, const struct PmdGbaFrame *frame)
{
    enum BattlerPosition position;
    u8 slot;

    if (frame == NULL || frame->gfx == NULL || battler >= gBattlersCount)
        return FALSE;
    if (gMonSpritesGfxPtr == NULL)
        return FALSE;

    position = GetBattlerPosition(battler);
    if (gMonSpritesGfxPtr->spritesGfx[position] == NULL)
        return FALSE;

    for (slot = 0; slot < PMD_GBA_CACHE_SLOTS; slot++)
    {
        u8 *dest = gMonSpritesGfxPtr->spritesGfx[position] + slot * MON_PIC_SIZE;
        DecompressDataWithHeaderWram(frame->gfx, dest);
    }
    return TRUE;
}

bool32 PmdSoulGold_PrimeTemplateBody(u8 battler, const struct PmdGbaFrame *frame)
{
    enum BattlerPosition position;

    if (frame == NULL || frame->gfx == NULL || battler >= gBattlersCount)
        return FALSE;
    if (gMonSpritesGfxPtr == NULL)
        return FALSE;

    position = GetBattlerPosition(battler);
    if (gMultiuseSpriteTemplate.images != gMonSpritesGfxPtr->frameImages[position])
        return FALSE;

    return PrimeImageArray(gMultiuseSpriteTemplate.images, frame);
}

bool32 PmdSoulGold_PrimeCreatedSpriteBody(u8 battler, const struct PmdGbaFrame *frame)
{
    enum BattlerPosition position;
    u8 spriteId;
    struct Sprite *sprite;

    if (frame == NULL || frame->gfx == NULL || battler >= gBattlersCount)
        return FALSE;
    if (gMonSpritesGfxPtr == NULL)
        return FALSE;

    spriteId = gBattlerSpriteIds[battler];
    if (spriteId >= MAX_SPRITES || !gSprites[spriteId].inUse)
        return FALSE;

    position = GetBattlerPosition(battler);
    sprite = &gSprites[spriteId];
    if (sprite->images != gMonSpritesGfxPtr->frameImages[position])
        return FALSE;

    if (!PrimeImageArray(sprite->images, frame))
        return FALSE;

    RequestSpriteFrameImageCopy(0, sprite->oam.tileNum, sprite->images);
    return TRUE;
}

void PmdSoulGold_Init(void)
{
    u8 battler;
    u8 sheet;

    PmdGbaRuntime_Init(&sSoulGoldPmdHostOps);
    for (sheet = 0; sheet < ARRAY_COUNT(sPmdGroundShadowSheets); sheet++)
        LoadSpriteSheet(&sPmdGroundShadowSheets[sheet]);

    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        sPmdGroundShadowSpriteIds[battler] = SPRITE_NONE;
        sNativeShadowSuppressed[battler] = FALSE;
        sActiveShadowProfiles[battler] = NULL;
    }
}

void PmdSoulGold_Reset(void)
{
    u8 battler;

    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        u8 spriteId = sPmdGroundShadowSpriteIds[battler];
        if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
            DestroySprite(&gSprites[spriteId]);
        sPmdGroundShadowSpriteIds[battler] = SPRITE_NONE;
        sNativeShadowSuppressed[battler] = FALSE;
        sActiveShadowProfiles[battler] = NULL;
    }
    FreeSpriteTilesByTag(TAG_PMD_CYNDAQUIL_GROUND_SHADOW_TILE);
    FreeSpriteTilesByTag(TAG_PMD_MARILL_GROUND_SHADOW_TILE);
    PmdGbaRuntime_Reset();
}
