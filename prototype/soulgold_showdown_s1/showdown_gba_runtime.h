#ifndef GUARD_SHOWDOWN_GBA_RUNTIME_H
#define GUARD_SHOWDOWN_GBA_RUNTIME_H

#include "global.h"

#define SHOWDOWN_GBA_CACHE_SLOTS 2
#define SHOWDOWN_GBA_MAX_BATTLERS 4

struct ShowdownGbaFrame
{
    const void *gfx;
    u16 duration;
};

struct ShowdownGbaAction
{
    const struct ShowdownGbaFrame *frames;
    u16 frameCount;
    bool8 loop;
};

struct ShowdownGbaHostOps
{
    bool32 (*CanPresentBattler)(u8 battler);
    bool32 (*StageFrame)(u8 battler, u8 cacheSlot, const struct ShowdownGbaFrame *frame);
    void (*PresentSlot)(u8 battler, u8 cacheSlot);
};

void ShowdownGbaRuntime_Init(const struct ShowdownGbaHostOps *host);
void ShowdownGbaRuntime_Reset(void);
bool32 ShowdownGbaRuntime_Bind(u8 battler, const struct ShowdownGbaAction *action);
void ShowdownGbaRuntime_Unbind(u8 battler);
void ShowdownGbaRuntime_Tick(void);

#endif // GUARD_SHOWDOWN_GBA_RUNTIME_H
