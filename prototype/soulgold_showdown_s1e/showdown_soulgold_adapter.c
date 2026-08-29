#include "global.h"
#include "battle.h"
#include "battle_interface.h"
#include "battle_main.h"
#include "data.h"
#include "decompress.h"
#include "pokemon.h"
#include "sprite.h"
#include "showdown_gba_runtime.h"
#include "showdown_soulgold_adapter.h"

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

    // S1D inherited the conservative Dummy-callback whitelist. PMD G3R4
    // proved that opponent front sprites can retain a native species callback
    // after move selection. Explicit battle-animation state is the ownership
    // boundary; callback identity is not.
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

static bool32 SoulGold_StageFrame(u8 battler, u8 cacheSlot, const struct ShowdownGbaFrame *frame)
{
    enum BattlerPosition position;
    u8 *dest;

    if (frame == NULL || frame->gfx == NULL || cacheSlot >= SHOWDOWN_GBA_CACHE_SLOTS)
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

    if (spriteId >= MAX_SPRITES || cacheSlot >= SHOWDOWN_GBA_CACHE_SLOTS)
        return;

    sprite = &gSprites[spriteId];
    if (sprite->images == NULL)
        return;

    RequestSpriteFrameImageCopy(cacheSlot, sprite->oam.tileNum, sprite->images);
}

static const struct ShowdownGbaHostOps sSoulGoldShowdownHostOps =
{
    .CanPresentBattler = SoulGold_CanPresentBattler,
    .StageFrame = SoulGold_StageFrame,
    .PresentSlot = SoulGold_PresentSlot,
};

static bool32 PrimeImageArray(const struct SpriteFrameImage *images, const struct ShowdownGbaFrame *frame)
{
    u8 slot;

    if (images == NULL || frame == NULL || frame->gfx == NULL)
        return FALSE;

    for (slot = 0; slot < SHOWDOWN_GBA_CACHE_SLOTS; slot++)
    {
        if (images[slot].data == NULL || images[slot].relativeFrames || images[slot].size < MON_PIC_SIZE)
            return FALSE;
    }

    for (slot = 0; slot < SHOWDOWN_GBA_CACHE_SLOTS; slot++)
        DecompressDataWithHeaderWram(frame->gfx, (void *)images[slot].data);

    return TRUE;
}

bool32 ShowdownSoulGold_PrimeLoadedBody(u8 battler, const struct ShowdownGbaFrame *frame)
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

    for (slot = 0; slot < SHOWDOWN_GBA_CACHE_SLOTS; slot++)
    {
        u8 *dest = gMonSpritesGfxPtr->spritesGfx[position] + slot * MON_PIC_SIZE;
        DecompressDataWithHeaderWram(frame->gfx, dest);
    }

    return TRUE;
}

bool32 ShowdownSoulGold_PrimeTemplateBody(u8 battler, const struct ShowdownGbaFrame *frame)
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

bool32 ShowdownSoulGold_PrimeCreatedSpriteBody(u8 battler, const struct ShowdownGbaFrame *frame)
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

    // Backing RAM alone is not first-visible ownership. Re-prime both resident
    // image slots and explicitly queue Showdown HOME/idle frame 0 into the
    // freshly-created OBJ before native send-out code can expose old pixels.
    if (!PrimeImageArray(sprite->images, frame))
        return FALSE;

    RequestSpriteFrameImageCopy(0, sprite->oam.tileNum, sprite->images);
    return TRUE;
}

void ShowdownSoulGold_PrepareOam(u8 battler)
{
    u8 spriteId;
    u8 healthboxId;
    u8 healthboxOtherId;
    u8 healthbarId;
    struct Sprite *sprite;
    struct Sprite *healthbox;

    if (!SoulGold_CanPresentBattler(battler))
        return;

    // AnimateSprites runs before BuildOamBuffer. Become the final spatial
    // writer only while Showdown owns idle presentation, so native send-out,
    // move, hit and faint choreography remain untouched.
    spriteId = gBattlerSpriteIds[battler];
    sprite = &gSprites[spriteId];
    sprite->x2 = 0;
    sprite->y2 = 0;

    healthboxId = gHealthboxSpriteIds[battler];
    if (healthboxId >= MAX_SPRITES || !gSprites[healthboxId].inUse)
        return;

    InitBattlerHealthboxCoords(battler);
    healthbox = &gSprites[healthboxId];
    healthbox->x2 = 0;
    healthbox->y2 = 0;

    healthboxOtherId = healthbox->oam.affineParam;
    if (healthboxOtherId < MAX_SPRITES && gSprites[healthboxOtherId].inUse)
    {
        gSprites[healthboxOtherId].x = healthbox->x + 64;
        gSprites[healthboxOtherId].y = healthbox->y;
        gSprites[healthboxOtherId].x2 = 0;
        gSprites[healthboxOtherId].y2 = 0;
    }

    // battle_interface.c stores the companion health-bar sprite id in data[5]
    // of the main healthbox. Mirror its normal callback position here because
    // that callback already ran earlier in AnimateSprites this tick.
    healthbarId = healthbox->data[5];
    if (healthbarId < MAX_SPRITES && gSprites[healthbarId].inUse)
    {
        gSprites[healthbarId].x = healthbox->x + (IsOnPlayerSide(battler) ? 16 : 8);
        gSprites[healthbarId].y = healthbox->y;
        gSprites[healthbarId].x2 = 0;
        gSprites[healthbarId].y2 = 0;
    }
}

void ShowdownSoulGold_Init(void)
{
    ShowdownGbaRuntime_Init(&sSoulGoldShowdownHostOps);
}

void ShowdownSoulGold_Reset(void)
{
    ShowdownGbaRuntime_Reset();
}
