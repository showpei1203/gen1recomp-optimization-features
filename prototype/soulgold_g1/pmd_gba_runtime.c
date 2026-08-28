#include "pmd_gba_runtime.h"

struct PmdGbaBattlerState
{
    const struct PmdGbaAction *action;
    u16 ticksLeft;
    u8 frameIndex;
    u8 visibleSlot;
    bool8 active;
    bool8 started;
    bool8 needsRefresh;
};

static const struct PmdGbaHostOps *sHost;
static struct PmdGbaBattlerState sBattlers[PMD_GBA_MAX_BATTLERS];

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
    state->ticksLeft = MAX(1, frame->duration);
    state->started = TRUE;
    state->needsRefresh = FALSE;
    return TRUE;
}

static bool32 RefreshCurrentFrame(u8 battler)
{
    struct PmdGbaBattlerState *state = &sBattlers[battler];
    const struct PmdGbaFrame *frame;

    if (sHost == NULL || state->action == NULL || !state->started)
        return FALSE;
    if (state->frameIndex >= state->action->frameCount)
        return FALSE;

    frame = &state->action->frames[state->frameIndex];
    if (!sHost->StageFrame(battler, state->visibleSlot, frame))
        return FALSE;

    sHost->PresentSlot(battler, state->visibleSlot);
    sHost->SetPresentationOffset(battler, frame->presentationX, frame->presentationY);
    state->needsRefresh = FALSE;
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
        sBattlers[battler].action = NULL;
        sBattlers[battler].ticksLeft = 0;
        sBattlers[battler].frameIndex = 0;
        sBattlers[battler].visibleSlot = 0;
        sBattlers[battler].active = FALSE;
        sBattlers[battler].started = FALSE;
        sBattlers[battler].needsRefresh = FALSE;
    }
}

bool32 PmdGbaRuntime_Bind(u8 battler, const struct PmdGbaAction *action)
{
    struct PmdGbaBattlerState *state;

    if (sHost == NULL || action == NULL || action->frames == NULL || action->frameCount == 0)
        return FALSE;
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return FALSE;

    // Binding establishes PMD ownership/state only. The host may still be in
    // send-out, switch, reshow or another native presentation phase. Tick waits
    // until CanPresentBattler() becomes true before uploading the first frame.
    state = &sBattlers[battler];
    state->action = action;
    state->ticksLeft = 0;
    state->frameIndex = 0;
    state->visibleSlot = 0;
    state->active = TRUE;
    state->started = FALSE;
    state->needsRefresh = FALSE;
    return TRUE;
}

void PmdGbaRuntime_Unbind(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;

    sBattlers[battler].action = NULL;
    sBattlers[battler].ticksLeft = 0;
    sBattlers[battler].frameIndex = 0;
    sBattlers[battler].visibleSlot = 0;
    sBattlers[battler].active = FALSE;
    sBattlers[battler].started = FALSE;
    sBattlers[battler].needsRefresh = FALSE;

    if (sHost != NULL)
        sHost->SetPresentationOffset(battler, 0, 0);
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
            // Native presentation may replace the battler's OBJ pixels or its
            // backing buffers. Pause PMD visible time and force a current-frame
            // refresh after native ownership releases.
            if (state->started)
                state->needsRefresh = TRUE;
            continue;
        }

        if (!state->started)
        {
            StageAndPresent(battler, 0, 0);
            continue;
        }

        if (state->needsRefresh)
        {
            RefreshCurrentFrame(battler);
            continue;
        }

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
