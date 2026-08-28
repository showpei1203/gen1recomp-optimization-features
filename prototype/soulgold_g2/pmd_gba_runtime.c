#include "pmd_gba_runtime.h"

struct PmdGbaBattlerState
{
    const struct PmdGbaAction *action;
    u16 ticksLeft;
    u8 frameIndex;
    u8 visibleSlot;
    bool8 active;
    bool8 started;
    bool8 complete;
    bool8 interrupted;
};

static const struct PmdGbaHostOps *sHost;
static struct PmdGbaBattlerState sBattlers[PMD_GBA_MAX_BATTLERS];

static void ClearState(struct PmdGbaBattlerState *state, bool8 clearInterrupted)
{
    state->action = NULL;
    state->ticksLeft = 0;
    state->frameIndex = 0;
    state->visibleSlot = 0;
    state->active = FALSE;
    state->started = FALSE;
    state->complete = FALSE;
    if (clearInterrupted)
        state->interrupted = FALSE;
}

static bool32 StageAndPresent(u8 battler, u8 frameIndex, u8 slot)
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
    state->ticksLeft = frame->duration > 0 ? frame->duration : 1;
    state->started = TRUE;
    state->complete = FALSE;
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

    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        sBattlers[battler].interrupted = FALSE;
        ClearState(&sBattlers[battler], TRUE);
    }
}

bool32 PmdGbaRuntime_Bind(u8 battler, const struct PmdGbaAction *action)
{
    struct PmdGbaBattlerState *state;

    if (sHost == NULL || action == NULL || action->frames == NULL || action->frameCount == 0)
        return FALSE;
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return FALSE;

    state = &sBattlers[battler];
    ClearState(state, TRUE);
    state->action = action;
    state->active = TRUE;
    return TRUE;
}

void PmdGbaRuntime_Unbind(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;

    // Never write host sprite state while unbinding. The battler slot may have
    // already been replaced by a native send-out/switch sprite.
    ClearState(&sBattlers[battler], TRUE);
}

bool32 PmdGbaRuntime_IsComplete(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return FALSE;
    return sBattlers[battler].complete;
}

bool32 PmdGbaRuntime_IsPresenting(u8 battler)
{
    struct PmdGbaBattlerState *state;

    if (battler >= PMD_GBA_MAX_BATTLERS || sHost == NULL)
        return FALSE;
    state = &sBattlers[battler];
    if (!state->active || !state->started || state->action == NULL)
        return FALSE;
    return sHost->CanPresentBattler(battler);
}

bool32 PmdGbaRuntime_ConsumeInterrupted(u8 battler)
{
    bool8 interrupted;

    if (battler >= PMD_GBA_MAX_BATTLERS)
        return FALSE;

    interrupted = sBattlers[battler].interrupted;
    sBattlers[battler].interrupted = FALSE;
    return interrupted;
}

void PmdGbaRuntime_Tick(void)
{
    u8 battler;

    if (sHost == NULL)
        return;

    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        struct PmdGbaBattlerState *state = &sBattlers[battler];
        u8 nextFrame;
        u8 nextSlot;

        if (!state->active || state->action == NULL)
            continue;

        if (!sHost->CanPresentBattler(battler))
        {
            // G2 ownership rule: once PMD has visibly started an ambient action,
            // any native ownership transition abandons that action completely.
            // It must never refresh/resume a stale mid-action frame later.
            if (state->started)
            {
                ClearState(state, FALSE);
                state->interrupted = TRUE;
            }
            continue;
        }

        if (!state->started)
        {
            StageAndPresent(battler, 0, 0);
            continue;
        }

        if (state->complete)
            continue;

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
                state->complete = TRUE;
                state->ticksLeft = 1;
                continue;
            }
            nextFrame = 0;
        }

        nextSlot = state->visibleSlot ^ 1;
        StageAndPresent(battler, nextFrame, nextSlot);
    }
}
