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

    // G3R3 incorrectly whitelisted only SpriteCallbackDummy/Dummy_2. Opponent
    // front sprites may retain a native species animation callback even after
    // the battle has reached move selection, which permanently denied PMD
    // ownership to Marill. At move selection, the explicit battle-animation
    // flags below are the ownership boundary; callback identity is not.
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

    // RAM priming is not presentation. G3R3 proved this the hard way: the
    // backing image slots contained PMD HOME, but the freshly-created battler
    // could still expose the previously loaded native OBJ pixels. Re-prime the
    // two backing slots and explicitly queue HOME into the created sprite's OBJ
    // VRAM before native send-out code is allowed to make it visible.
    if (!PrimeImageArray(sprite->images, frame))
        return FALSE;

    RequestSpriteFrameImageCopy(0, sprite->oam.tileNum, sprite->images);
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
