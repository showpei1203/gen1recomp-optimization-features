#ifndef GUARD_PMD_SOULGOLD_ADAPTER_H
#define GUARD_PMD_SOULGOLD_ADAPTER_H

#include "pmd_gba_runtime.h"

void PmdSoulGold_Init(void);
void PmdSoulGold_Reset(void);
bool32 PmdSoulGold_PrimeBodyFrame(u8 battler, const struct PmdGbaFrame *frame);

#endif // GUARD_PMD_SOULGOLD_ADAPTER_H
