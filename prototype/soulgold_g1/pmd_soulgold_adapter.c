#include "global.h"
#include "battle.h"
#include "data.h"
#include "decompress.h"
#include "pokemon.h"
#include "sprite.h"
#include "pmd_gba_runtime.h"

// G1 candidate only.
// This adapter intentionally proves the existing two-slot battler buffer path
// before combat ownership / Rich Ambient sequencing are added.

static bool32 SoulGold_CanPresentBattler(enum BattlerId battler)
{
    u8 spriteId;

    if (battler >= gBattlersCount)
        return FALSE;
    if (gMonSpritesGfxPtr == NULL || gBattleSpritesDataPtr == NULL)
        return FALSE;

    spriteId = gBattlerSpriteIds[battler];
    if (spriteId >= MAX_SPRITES || !gSprites[spriteId].inUse || gSprites[spriteId].invisible)
        return FALSE;

    // G1 must not fight existing battle-presentation owners.
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

static bool32 SoulGold_StageFrame(enum BattlerId battler, u8 cacheSlot, const struct PmdGbaFrame *frame)
{
    enum BattlerPosition position;
    u8 *dest;

    if (frame == NULL || frame->gfx == NULL || cacheSlot >= PMD_GBA_CACHE_SLOTS)
        return FALSE;
    if (gMonSpritesGfxPtr == NULL)
        return FALSE;

    position = GetBattlerPosition(battler);
    dest = gMonSpritesGfxPtr->spritesGfx[position] + cacheSlot * MON_PIC_SIZE;

    // Converter contract for G1:
    // every source blob expands to exactly one normalized 64x64 4bpp frame
    // (MON_PIC_SIZE bytes).  DecompressDataWithHeaderWram keeps this compatible
    // with SoulGold's existing compressed graphics loaders.
    DecompressDataWithHeaderWram(frame->gfx, dest);
    return TRUE;
}

static void SoulGold_PresentSlot(enum BattlerId battler, u8 cacheSlot)
{
    u8 spriteId = gBattlerSpriteIds[battler];
    struct Sprite *sprite;

    if (spriteId >= MAX_SPRITES || cacheSlot >= PMD_GBA_CACHE_SLOTS)
        return;

    sprite = &gSprites[spriteId];

    // Opponent species frontAnimFrames may expose only animation 0.  PMD
    // rolling-cache presentation always uses the generic 0/1 frame table after
    // the stock entry animation has released ownership.
    sprite->anims = gAnims_MonPic;
    StartSpriteAnim(sprite, cacheSlot);
}

static void SoulGold_SetPresentationOffset(enum BattlerId battler, s16 x, s16 y)
{
    u8 spriteId = gBattlerSpriteIds[battler];

    if (spriteId >= MAX_SPRITES)
        return;

    // G1 uses x2/y2 only while SoulGold_CanPresentBattler() is true.
    // G2 must introduce explicit HOME/suspend ownership before combat actions
    // are allowed to coexist with non-zero PMD presentation offsets.
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

void PmdSoulGold_Init(void)
{
    PmdGbaRuntime_Init(&sSoulGoldPmdHostOps);
}

void PmdSoulGold_Reset(void)
{
    PmdGbaRuntime_Reset();
}
