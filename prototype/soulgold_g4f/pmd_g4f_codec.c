#include "global.h"
#include "decompress.h"
#include "pmd_gba_runtime.h"
#include "pmd_g4f_codec.h"
#include <string.h>

/* G4F intentionally sizes its EWRAM workspace for the two-profile runtime
 * pilot, not the eventual 901-species ceiling. The asset generator refuses a
 * pack that exceeds these bounds. That keeps this proof from casually eating a
 * quarter of EWRAM merely because an offline audit once said it technically fit. */
EWRAM_DATA static u8 sDictionary[PMD_GBA_MAX_BATTLERS][PMD_G4F_MAX_DICTIONARY_BYTES] = {};
EWRAM_DATA static u8 sCommands[PMD_GBA_MAX_BATTLERS][PMD_G4F_MAX_COMMAND_BYTES] = {};
EWRAM_DATA static u8 sBodyScratch[PMD_GBA_MAX_BATTLERS][PMD_G4F_FRAME_BYTES] = {};

static const struct PmdG4fPackedAction *sLoadedAction[PMD_GBA_MAX_BATTLERS];
static u8 sDecodedThrough[PMD_GBA_MAX_BATTLERS];
static bool8 sLoaded[PMD_GBA_MAX_BATTLERS];

static bool32 IsValidAction(const struct PmdG4fPackedAction *action)
{
    if (action == NULL
     || action->dictionaryLz == NULL
     || action->homeMap == NULL
     || action->commandsLz == NULL
     || action->frameOffsets == NULL)
        return FALSE;
    if (action->indexWidth != 1 || action->frameCount == 0)
        return FALSE;
    if (action->dictionaryBytes == 0
     || action->dictionaryBytes > PMD_G4F_MAX_DICTIONARY_BYTES
     || action->dictionaryBytes % PMD_G4F_TILE_BYTES != 0)
        return FALSE;
    if (action->commandBytes == 0 || action->commandBytes > PMD_G4F_MAX_COMMAND_BYTES)
        return FALSE;
    return TRUE;
}

void PmdG4fCodec_ResetBattler(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;
    sLoadedAction[battler] = NULL;
    sDecodedThrough[battler] = 0xFF;
    sLoaded[battler] = FALSE;
}

void PmdG4fCodec_Reset(void)
{
    u8 battler;
    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
        PmdG4fCodec_ResetBattler(battler);
}

static bool32 BuildHome(u8 battler, const struct PmdG4fPackedAction *action)
{
    u16 dictionaryEntries = action->dictionaryBytes / PMD_G4F_TILE_BYTES;
    u8 tilePos;

    memset(sBodyScratch[battler], 0, PMD_G4F_FRAME_BYTES);
    for (tilePos = 0; tilePos < PMD_G4F_TILES_PER_FRAME; tilePos++)
    {
        u8 tileIndex = action->homeMap[tilePos];
        u8 *dest = &sBodyScratch[battler][tilePos * PMD_G4F_TILE_BYTES];
        if (tileIndex == 0)
            continue;
        if (tileIndex > dictionaryEntries)
            return FALSE;
        memcpy(dest,
               &sDictionary[battler][(tileIndex - 1) * PMD_G4F_TILE_BYTES],
               PMD_G4F_TILE_BYTES);
    }
    return TRUE;
}

static bool32 LoadAction(u8 battler, const struct PmdG4fPackedAction *action)
{
    if (!IsValidAction(action))
        return FALSE;

    DecompressDataWithHeaderWram(action->dictionaryLz, sDictionary[battler]);
    DecompressDataWithHeaderWram(action->commandsLz, sCommands[battler]);
    if (!BuildHome(battler, action))
        return FALSE;

    sLoadedAction[battler] = action;
    sDecodedThrough[battler] = 0xFF;
    sLoaded[battler] = TRUE;
    return TRUE;
}

static bool32 ApplyFrameDelta(u8 battler, const struct PmdG4fPackedAction *action, u8 frameIndex)
{
    u16 dictionaryEntries = action->dictionaryBytes / PMD_G4F_TILE_BYTES;
    u16 cursor;
    u8 count;
    u8 i;

    if (frameIndex >= action->frameCount)
        return FALSE;
    cursor = action->frameOffsets[frameIndex];
    if (cursor >= action->commandBytes)
        return FALSE;

    count = sCommands[battler][cursor++];
    for (i = 0; i < count; i++)
    {
        u8 tilePos;
        u8 tileIndex;
        u8 *dest;
        if (cursor + 2 > action->commandBytes)
            return FALSE;
        tilePos = sCommands[battler][cursor++];
        tileIndex = sCommands[battler][cursor++];
        if (tilePos >= PMD_G4F_TILES_PER_FRAME || tileIndex > dictionaryEntries)
            return FALSE;
        dest = &sBodyScratch[battler][tilePos * PMD_G4F_TILE_BYTES];
        if (tileIndex == 0)
            memset(dest, 0, PMD_G4F_TILE_BYTES);
        else
            memcpy(dest,
                   &sDictionary[battler][(tileIndex - 1) * PMD_G4F_TILE_BYTES],
                   PMD_G4F_TILE_BYTES);
    }
    sDecodedThrough[battler] = frameIndex;
    return TRUE;
}

bool32 PmdG4fCodec_DecodeFrame(u8 battler, const struct PmdG4fPackedFrame *frame, void *dest)
{
    const struct PmdG4fPackedAction *action;
    u8 start;
    u8 i;

    if (battler >= PMD_GBA_MAX_BATTLERS || frame == NULL || dest == NULL)
        return FALSE;
    action = frame->action;
    if (!IsValidAction(action) || frame->frameIndex >= action->frameCount)
        return FALSE;

    /* A new action, frame zero, or any non-sequential request rebuilds from
     * HOME. This makes interruption/rebind deterministic instead of depending
     * on stale decoder history. All of this runs in PmdGbaRuntime_Prepare(),
     * before AnimateSprites and outside the OAM presentation window. */
    if (!sLoaded[battler]
     || sLoadedAction[battler] != action
     || frame->frameIndex == 0
     || (sDecodedThrough[battler] != 0xFF && frame->frameIndex != (u8)(sDecodedThrough[battler] + 1)))
    {
        if (!LoadAction(battler, action))
            return FALSE;
    }

    start = sDecodedThrough[battler] == 0xFF ? 0 : (u8)(sDecodedThrough[battler] + 1);
    for (i = start; i <= frame->frameIndex; i++)
    {
        if (!ApplyFrameDelta(battler, action, i))
        {
            PmdG4fCodec_ResetBattler(battler);
            return FALSE;
        }
    }

    memcpy(dest, sBodyScratch[battler], PMD_G4F_FRAME_BYTES);
    return TRUE;
}
