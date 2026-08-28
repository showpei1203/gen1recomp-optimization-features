#include "global.h"
#include "battle.h"
#include "battle_main.h"
#include "data.h"
#include "decompress.h"
#include "pokemon.h"
#include "sprite.h"
#include "pmd_gba_runtime.h"
#include "pmd_soulgold_adapter.h"

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

    if (sprite->callback != SpriteCallbackDummy
     && sprite->callback != SpriteCallbackDummy_2)
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

    // Ownership boundary: this path may touch ONLY the canonical backing buffer
    // for this battler position. It must never modify gMultiuseSpriteTemplate or
    // another live sprite. BattleLoadMonSpriteGfx() calls this after native data
    // has loaded, so PMD becomes the final body writer for supported battlers.
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

    // Ownership boundary: this path is valid only immediately after
    // SetMultiuseSpriteTemplateToPokemon() for this battler. Requiring the exact
    // frameImages pointer prevents a stale trainer/other-battler template from
    // being overwritten. No canonical/live-sprite writes happen here.
    if (gMultiuseSpriteTemplate.images != gMonSpritesGfxPtr->frameImages[position])
        return FALSE;

    return PrimeImageArray(gMultiuseSpriteTemplate.images, frame);
}

void PmdSoulGold_Init(void)
{
    PmdGbaRuntime_Init(&sSoulGoldPmdHostOps);
}

void PmdSoulGold_Reset(void)
{
    PmdGbaRuntime_Reset();
}
