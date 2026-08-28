#ifndef GUARD_PMD_SOULGOLD_DYNAMIC_SHADOW_H
#define GUARD_PMD_SOULGOLD_DYNAMIC_SHADOW_H

#include "global.h"

struct PmdSoulGoldShadowFrame
{
    u16 tileOffset;
    s8 xOffset;
    s8 yOffset;
};

struct PmdSoulGoldShadowAction
{
    const struct PmdSoulGoldShadowFrame *frames;
    u8 frameCount;
};

void PmdSoulGoldDynamicShadow_Init(void);
void PmdSoulGoldDynamicShadow_Reset(void);
void PmdSoulGoldDynamicShadow_Update(
    u8 battler,
    bool32 active,
    const struct PmdSoulGoldShadowAction *action,
    u8 frameIndex);

#endif // GUARD_PMD_SOULGOLD_DYNAMIC_SHADOW_H
