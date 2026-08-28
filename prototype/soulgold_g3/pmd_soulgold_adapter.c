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

bool32 PmdSoulGold_PrimeBodyFrame(u8 battler, const struct PmdGbaFrame *frame)
{
    u8 slot;
    const struct SpriteFrameImage *images;

    if (frame == NULL || frame->gfx == NULL)
        return FALSE;
    if (battler >= gBattlersCount)
        return FALSE;

    // This function is called immediately after
    // SetMultiuseSpriteTemplateToPokemon() and immediately before CreateSprite().
    // Therefore gMultiuseSpriteTemplate.images is the authoritative image array
    // for the exact Pokemon sprite that SoulGold is about to create. Do not
    // assume gMonSpritesGfxPtr owns that array at this point: SoulGold may use
    // another MonSpritesGfxManager while preparing send-out graphics.
    images = gMultiuseSpriteTemplate.images;
    if (images == NULL)
        return FALSE;

    // Both resident image slots must be real full-mon frame buffers. The image
    // descriptors are const metadata, but their data pointers refer to the
    // writable EWRAM backing buffers managed by SoulGold.
    for (slot = 0; slot < PMD_GBA_CACHE_SLOTS; slot++)
    {
        if (images[slot].data == NULL)
            return FALSE;
        if (images[slot].relativeFrames)
            return FALSE;
        if (images[slot].size < MON_PIC_SIZE)
            return FALSE;
    }

    // G3R1 send-out rule: prime the exact image buffers that CreateSprite() will
    // consume. Both frame indices receive the same PMD HOME body+shadow frame,
    // so native send-out frame 0/1 transitions cannot expose the legacy body.
    for (slot = 0; slot < PMD_GBA_CACHE_SLOTS; slot++)
        DecompressDataWithHeaderWram(frame->gfx, (void *)images[slot].data);

    return TRUE;
}

void PmdSoulGold_Init(void)
{
    PmdGbaRuntime_Init(&sSoulGoldPmdHostOps);
}

void PmdSoulGold_Reset(void)
{
    PmdGbaRuntime_Reset();
}
