#include "global.h"
#include "battle.h"
#include "battle_interface.h"
#include "battle_main.h"
#include "data.h"
#include "decompress.h"
#include "pokemon.h"
#include "sprite.h"
#include "pmd_gba_runtime.h"
#include "pmd_soulgold_adapter.h"

// SoulGold's normal single enemy shadow is already a compact 32x8 asset. G3R5
// loads that artwork under a private tile tag and owns one shadow OBJ per PMD
// battler. This avoids the Gen4-style two-half (up to 64 px) enemy shadow and,
// unlike the native shadow callback, works for the player side as well.
extern const u32 gEnemyMonShadow_Gfx[];

#define TAG_PMD_GROUND_SHADOW_TILE 0xF3D5
#define PMD_GROUND_SHADOW_Y_OFFSET 29

static u8 sPmdGroundShadowSpriteIds[PMD_GBA_MAX_BATTLERS];

static const struct CompressedSpriteSheet sPmdGroundShadowSheet =
{
    .data = gEnemyMonShadow_Gfx,
    .size = 0x80,
    .tag = TAG_PMD_GROUND_SHADOW_TILE,
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

static const struct SpriteTemplate sPmdGroundShadowTemplate =
{
    .tileTag = TAG_PMD_GROUND_SHADOW_TILE,
    .paletteTag = TAG_SHADOW_PAL,
    .oam = &sPmdGroundShadowOam,
    .anims = sPmdGroundShadowAnims,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};

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

static void HideNativeShadow(u8 battler)
{
    u8 spriteId;

    if (gBattleSpritesDataPtr == NULL || battler >= gBattlersCount)
        return;

    spriteId = gBattleSpritesDataPtr->healthBoxesData[battler].shadowSpriteIdPrimary;
    if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
    {
        gSprites[spriteId].callback = SpriteCallbackDummy;
        gSprites[spriteId].invisible = TRUE;
    }

    spriteId = gBattleSpritesDataPtr->healthBoxesData[battler].shadowSpriteIdSecondary;
    if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
    {
        gSprites[spriteId].callback = SpriteCallbackDummy;
        gSprites[spriteId].invisible = TRUE;
    }
}

void PmdSoulGold_UpdateGroundShadow(u8 battler, bool32 active)
{
    u8 bodySpriteId;
    u8 shadowSpriteId;
    struct Sprite *body;
    struct Sprite *shadow;

    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;

    HideNativeShadow(battler);

    shadowSpriteId = sPmdGroundShadowSpriteIds[battler];
    if (!active || battler >= gBattlersCount)
    {
        if (shadowSpriteId < MAX_SPRITES && gSprites[shadowSpriteId].inUse)
            gSprites[shadowSpriteId].invisible = TRUE;
        return;
    }

    bodySpriteId = gBattlerSpriteIds[battler];
    if (bodySpriteId >= MAX_SPRITES || !gSprites[bodySpriteId].inUse)
    {
        if (shadowSpriteId < MAX_SPRITES && gSprites[shadowSpriteId].inUse)
            gSprites[shadowSpriteId].invisible = TRUE;
        return;
    }
    body = &gSprites[bodySpriteId];

    if (shadowSpriteId >= MAX_SPRITES || !gSprites[shadowSpriteId].inUse)
    {
        shadowSpriteId = CreateSprite(&sPmdGroundShadowTemplate, body->x, body->y + PMD_GROUND_SHADOW_Y_OFFSET, 0xC8);
        if (shadowSpriteId >= MAX_SPRITES)
        {
            sPmdGroundShadowSpriteIds[battler] = SPRITE_NONE;
            return;
        }
        sPmdGroundShadowSpriteIds[battler] = shadowSpriteId;
    }

    shadow = &gSprites[shadowSpriteId];
    shadow->callback = SpriteCallbackDummy;
    // The ground layer follows the battler's base battlefield coordinate only.
    // PMD frame-specific x2/y2 stabilization must never drag the shadow around.
    shadow->x = body->x;
    shadow->y = body->y + PMD_GROUND_SHADOW_Y_OFFSET;
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

    PmdGbaRuntime_Init(&sSoulGoldPmdHostOps);
    LoadCompressedSpriteSheet(&sPmdGroundShadowSheet);
    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
        sPmdGroundShadowSpriteIds[battler] = SPRITE_NONE;
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
    }
    FreeSpriteTilesByTag(TAG_PMD_GROUND_SHADOW_TILE);
    PmdGbaRuntime_Reset();
}
