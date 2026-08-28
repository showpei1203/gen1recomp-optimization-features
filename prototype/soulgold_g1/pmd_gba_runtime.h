#ifndef GUARD_PMD_GBA_RUNTIME_H
#define GUARD_PMD_GBA_RUNTIME_H

#include "global.h"

#define PMD_GBA_CACHE_SLOTS 2

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
    bool32 (*CanPresentBattler)(enum BattlerId battler);
    bool32 (*StageFrame)(enum BattlerId battler, u8 cacheSlot, const struct PmdGbaFrame *frame);
    void (*PresentSlot)(enum BattlerId battler, u8 cacheSlot);
    void (*SetPresentationOffset)(enum BattlerId battler, s16 x, s16 y);
};

void PmdGbaRuntime_Init(const struct PmdGbaHostOps *host);
void PmdGbaRuntime_Reset(void);
bool32 PmdGbaRuntime_Bind(enum BattlerId battler, const struct PmdGbaAction *action);
void PmdGbaRuntime_Unbind(enum BattlerId battler);
void PmdGbaRuntime_Tick(void);

#endif // GUARD_PMD_GBA_RUNTIME_H
