#ifndef GUARD_SHOWDOWN_SOULGOLD_ADAPTER_H
#define GUARD_SHOWDOWN_SOULGOLD_ADAPTER_H

#include "global.h"
#include "showdown_gba_runtime.h"

bool32 ShowdownSoulGold_PrimeLoadedBody(u8 battler, const struct ShowdownGbaFrame *frame);
bool32 ShowdownSoulGold_PrimeTemplateBody(u8 battler, const struct ShowdownGbaFrame *frame);
bool32 ShowdownSoulGold_PrimeCreatedSpriteBody(u8 battler, const struct ShowdownGbaFrame *frame);
void ShowdownSoulGold_PrepareOam(u8 battler);
void ShowdownSoulGold_Init(void);
void ShowdownSoulGold_Reset(void);

#endif // GUARD_SHOWDOWN_SOULGOLD_ADAPTER_H
