#ifndef GUARD_PMD_G4F_CODEC_H
#define GUARD_PMD_G4F_CODEC_H

#include "global.h"

#define PMD_G4F_FRAME_BYTES 0x800
#define PMD_G4F_TILE_BYTES 32
#define PMD_G4F_TILES_PER_FRAME 64
#define PMD_G4F_MAX_DICTIONARY_BYTES 4096
#define PMD_G4F_MAX_COMMAND_BYTES 512

struct PmdG4fPackedAction
{
    const u32 *dictionaryLz;
    u16 dictionaryBytes;
    const u8 *homeMap;
    const u32 *commandsLz;
    u16 commandBytes;
    const u16 *frameOffsets;
    u8 indexWidth;
    u8 frameCount;
};

struct PmdG4fPackedFrame
{
    const struct PmdG4fPackedAction *action;
    u8 frameIndex;
};

void PmdG4fCodec_Reset(void);
void PmdG4fCodec_ResetBattler(u8 battler);
bool32 PmdG4fCodec_DecodeFrame(u8 battler, const struct PmdG4fPackedFrame *frame, void *dest);

#endif // GUARD_PMD_G4F_CODEC_H
