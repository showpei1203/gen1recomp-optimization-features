#include "pmd_gba_runtime.h"

struct PmdGbaBattlerState
{
    const struct PmdGbaAction *action;
    u16 ticksLeft;
    u8 frameIndex;
    u8 visibleSlot;
    bool8 active;
};

static const struct PmdGbaHostOps *sHost;
static struct PmdGbaBattlerState sBattlers[MAX_BATTLERS_COUNT];

static bool32 StageAndPresent(enum BattlerId battler, u8 frameIndex, u8 slot)
{
    struct PmdGbaBattlerState *state = &sBattlers[battler];
    const struct PmdGbaFrame *frame;

    if (sHost == NULL || state->action == NULL || frameIndex >= state->action->frameCount)
        return FALSE;

    frame = &state->action->frames[frameIndex];
    if (!sHost->StageFrame(battler, slot, frame))
        return FALSE;

    sHost->PresentSlot(battler, slot);
    sHost->SetPresentationOffset(battler, frame->presentationX, frame->presentationY);

    state->frameIndex = frameIndex;
    state->visibleSlot = slot;
    state->ticksLeft = MAX(1, frame->duration);
    return TRUE;
}

void PmdGbaRuntime_Init(const struct PmdGbaHostOps *host)
{
    sHost = host;
    PmdGbaRuntime_Reset();
}

void PmdGbaRuntime_Reset(void)
{
    u8 battler;

    for (battler = 0; battler < MAX_BATTLERS_COUNT; battler++)
    {
        sBattlers[battler].action = NULL;
        sBattlers[battler].ticksLeft = 0;
        sBattlers[battler].frameIndex = 0;
        sBattlers[battler].visibleSlot = 0;
        sBattlers[battler].active = FALSE;
    }
}

bool32 PmdGbaRuntime_Bind(enum BattlerId battler, const struct PmdGbaAction *action)
{
    struct PmdGbaBattlerState *state;

    if (sHost == NULL || action == NULL || action->frames == NULL || action->frameCount == 0)
        return FALSE;
    if (battler >= MAX_BATTLERS_COUNT || !sHost->CanPresentBattler(battler))
        return FALSE;

    state = &sBattlers[battler];
    state->action = action;
    state->ticksLeft = 0;
    state->frameIndex = 0;
    state->visibleSlot = 1; // first StageAndPresent writes slot 0
    state->active = TRUE;

    return StageAndPresent(battler, 0, 0);
}

void PmdGbaRuntime_Unbind(enum BattlerId battler)
{
    if (battler >= MAX_BATTLERS_COUNT)
        return;

    sBattlers[battler].action = NULL;
    sBattlers[battler].ticksLeft = 0;
    sBattlers[battler].frameIndex = 0;
    sBattlers[battler].visibleSlot = 0;
    sBattlers[battler].active = FALSE;

    if (sHost != NULL)
        sHost->SetPresentationOffset(battler, 0, 0);
}

void PmdGbaRuntime_Tick(void)
{
    enum BattlerId battler;

    if (sHost == NULL)
        return;

    for (battler = 0; battler < MAX_BATTLERS_COUNT; battler++)
    {
        struct PmdGbaBattlerState *state = &sBattlers[battler];
        u8 nextFrame;
        u8 nextSlot;

        if (!state->active || state->action == NULL)
            continue;
        if (!sHost->CanPresentBattler(battler))
            continue; // pause visible-time clock while host cannot safely present

        if (state->ticksLeft > 1)
        {
            state->ticksLeft--;
            continue;
        }

        nextFrame = state->frameIndex + 1;
        if (nextFrame >= state->action->frameCount)
        {
            if (!state->action->loop)
            {
                state->ticksLeft = 1;
                continue;
            }
            nextFrame = 0;
        }

        nextSlot = state->visibleSlot ^ 1;
        StageAndPresent(battler, nextFrame, nextSlot);
    }
}
