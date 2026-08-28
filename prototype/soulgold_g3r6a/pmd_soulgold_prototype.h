#ifndef GUARD_PMD_SOULGOLD_PROTOTYPE_H
#define GUARD_PMD_SOULGOLD_PROTOTYPE_H

#include "global.h"
#include "battle.h"

void PmdSoulGoldPrototype_Init(void);
void PmdSoulGoldPrototype_Tick(void);
void PmdSoulGoldPrototype_Reset(void);
void PmdSoulGoldPrototype_PrimeLoadedBattlerBody(u8 battler);
void PmdSoulGoldPrototype_PrimeTemplateBody(u8 battler, u16 species);
void PmdSoulGoldPrototype_PrimeCreatedSpriteBody(u8 battler, u16 species);

/* G3R6A: replacement visual handler for CONTROLLER_HITANIMATION on PMD-owned battlers. */
void PmdSoulGoldPrototype_HandleHitAnimation(enum BattlerId battler);

#endif // GUARD_PMD_SOULGOLD_PROTOTYPE_H
