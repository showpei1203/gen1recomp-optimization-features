#ifndef GUARD_SHOWDOWN_SOULGOLD_PROTOTYPE_H
#define GUARD_SHOWDOWN_SOULGOLD_PROTOTYPE_H

#include "global.h"

void ShowdownSoulGoldPrototype_PrimeLoadedBattlerBody(u8 battler);
void ShowdownSoulGoldPrototype_PrimeTemplateBody(u8 battler, u16 species);
void ShowdownSoulGoldPrototype_PrimeCreatedSpriteBody(u8 battler, u16 species);
void ShowdownSoulGoldPrototype_Init(void);
void ShowdownSoulGoldPrototype_PrepareOam(void);
void ShowdownSoulGoldPrototype_Tick(void);
void ShowdownSoulGoldPrototype_Reset(void);

#endif // GUARD_SHOWDOWN_SOULGOLD_PROTOTYPE_H
