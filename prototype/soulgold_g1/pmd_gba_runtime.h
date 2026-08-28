#ifndef GUARD_PMD_GBA_RUNTIME_H
#define GUARD_PMD_GBA_RUNTIME_H

#include "global.h"

#define PMD_GBA_CACHE_SLOTS 2
#define PMD_GBA_MAX_BATTLERS 4

struct PmdGbaFrame
{
    const void *gfx;
    u16 duration;
    s8 presentationX;
    s8 presentationY;
};

struct PmdGbaAction
{
    const struct PmdGbaFrame *frames;
    u8 frameCount;
    bool8 loop;
};

struct PmdGbaHostOps
{
    bool32 (*CanPresentBattler)(u8 battler);
    bool32 (*StageFrame)(u8 battler, u8 cacheSlot, const struct PmdGbaFrame *frame);
    void (*PresentSlot)(u8 battler, u8 cacheSlot);
    void (*SetPresentationOffset)(u8 battler, s16 x, s16 y);
};

void PmdGbaRuntime_Init(const struct PmdGbaHostOps *host);
void PmdGbaRuntime_Reset(void);
bool32 PmdGbaRuntime_Bind(u8 battler, const struct PmdGbaAction *action);
void PmdGbaRuntime_Unbind(u8 battler);
void PmdGbaRuntime_Tick(void);

#endif // GUARD_PMD_GBA_RUNTIME_H
