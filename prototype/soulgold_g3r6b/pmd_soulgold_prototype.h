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

/* G3R6A: semantic replacement for CONTROLLER_HITANIMATION on PMD profiles. */
void PmdSoulGoldPrototype_HandleHitAnimation(enum BattlerId battler);

/* G3R6B: body-only PMDCollab Attack layered under SoulGold's native move FX.
 * Begin is called immediately before DoMoveAnim(). End is called only after the
 * native animation script becomes inactive. The native controller must not
 * complete until IsMoveReturnReady() reports that PMD HOME is back in OBJ VRAM.
 */
void PmdSoulGoldPrototype_BeginMoveAction(enum BattlerId battler);
void PmdSoulGoldPrototype_EndMoveAction(enum BattlerId battler);
bool32 PmdSoulGoldPrototype_IsMoveReturnReady(enum BattlerId battler);

#endif // GUARD_PMD_SOULGOLD_PROTOTYPE_H
