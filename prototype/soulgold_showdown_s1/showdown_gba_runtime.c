#include "showdown_gba_runtime.h"

struct ShowdownGbaBattlerState
{
    const struct ShowdownGbaAction *action;
    u16 ticksLeft;
    u8 frameIndex;
    u8 visibleSlot;
    bool8 active;
    bool8 started;
    bool8 needsRefresh;
};

static const struct ShowdownGbaHostOps *sHost;
static struct ShowdownGbaBattlerState sBattlers[SHOWDOWN_GBA_MAX_BATTLERS];

static bool32 StageAndPresent(u8 battler, u8 frameIndex, u8 slot)
{
    struct ShowdownGbaBattlerState *state = &sBattlers[battler];
    const struct ShowdownGbaFrame *frame;

    if (sHost == NULL || state->action == NULL || frameIndex >= state->action->frameCount)
        return FALSE;

    frame = &state->action->frames[frameIndex];
    if (!sHost->StageFrame(battler, slot, frame))
        return FALSE;

    sHost->PresentSlot(battler, slot);
    state->frameIndex = frameIndex;
    state->visibleSlot = slot;
    state->ticksLeft = frame->duration > 0 ? frame->duration : 1;
    state->started = TRUE;
    state->needsRefresh = FALSE;
    return TRUE;
}

static bool32 RefreshCurrentFrame(u8 battler)
{
    struct ShowdownGbaBattlerState *state = &sBattlers[battler];
    const struct ShowdownGbaFrame *frame;

    if (sHost == NULL || state->action == NULL || !state->started)
        return FALSE;
    if (state->frameIndex >= state->action->frameCount)
        return FALSE;

    frame = &state->action->frames[state->frameIndex];
    if (!sHost->StageFrame(battler, state->visibleSlot, frame))
        return FALSE;

    sHost->PresentSlot(battler, state->visibleSlot);
    state->needsRefresh = FALSE;
    return TRUE;
}

void ShowdownGbaRuntime_Init(const struct ShowdownGbaHostOps *host)
{
    sHost = host;
    ShowdownGbaRuntime_Reset();
}

void ShowdownGbaRuntime_Reset(void)
{
    u8 battler;

    for (battler = 0; battler < SHOWDOWN_GBA_MAX_BATTLERS; battler++)
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

bool32 ShowdownGbaRuntime_Bind(u8 battler, const struct ShowdownGbaAction *action)
{
    struct ShowdownGbaBattlerState *state;

    if (sHost == NULL || action == NULL || action->frames == NULL || action->frameCount == 0)
        return FALSE;
    if (battler >= SHOWDOWN_GBA_MAX_BATTLERS)
        return FALSE;

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

void ShowdownGbaRuntime_Unbind(u8 battler)
{
    if (battler >= SHOWDOWN_GBA_MAX_BATTLERS)
        return;

    sBattlers[battler].action = NULL;
    sBattlers[battler].ticksLeft = 0;
    sBattlers[battler].frameIndex = 0;
    sBattlers[battler].visibleSlot = 0;
    sBattlers[battler].active = FALSE;
    sBattlers[battler].started = FALSE;
    sBattlers[battler].needsRefresh = FALSE;
}

void ShowdownGbaRuntime_Tick(void)
{
    u8 battler;

    if (sHost == NULL)
        return;

    for (battler = 0; battler < SHOWDOWN_GBA_MAX_BATTLERS; battler++)
    {
        struct ShowdownGbaBattlerState *state = &sBattlers[battler];
        u8 nextFrame;
        u8 nextSlot;

        if (!state->active || state->action == NULL)
            continue;

        if (!sHost->CanPresentBattler(battler))
        {
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
