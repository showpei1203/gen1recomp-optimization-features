#include "pmd_gba_runtime.h"
#include "pmd_g4f_codec.h"

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

    /* G4F two-phase presentation. StageFrame may decompress/reconstruct and is
     * therefore confined to PmdGbaRuntime_Prepare(), which SoulGold calls
     * before AnimateSprites(). Tick only commits a pre-staged slot after native
     * callbacks and before BuildOamBuffer(). */
    bool8 prepared;
    u8 preparedFrameIndex;
    u8 preparedSlot;
};

static const struct PmdGbaHostOps *sHost;
static struct PmdGbaBattlerState sBattlers[PMD_GBA_MAX_BATTLERS];

static void ClearPrepared(struct PmdGbaBattlerState *state)
{
    state->prepared = FALSE;
    state->preparedFrameIndex = 0;
    state->preparedSlot = 0;
}

static void ClearState(struct PmdGbaBattlerState *state, bool8 clearInterrupted)
{
    state->action = NULL;
    state->ticksLeft = 0;
    state->frameIndex = 0;
    state->visibleSlot = 0;
    state->active = FALSE;
    state->started = FALSE;
    state->complete = FALSE;
    ClearPrepared(state);
    if (clearInterrupted)
        state->interrupted = FALSE;
}

static bool32 GetPendingFrame(const struct PmdGbaBattlerState *state, u8 *frameIndex, u8 *slot)
{
    u8 nextFrame;

    if (!state->active || state->action == NULL || state->complete)
        return FALSE;

    if (!state->started)
    {
        *frameIndex = 0;
        *slot = 0;
        return TRUE;
    }

    if (state->ticksLeft > 1)
        return FALSE;

    nextFrame = state->frameIndex + 1;
    if (nextFrame >= state->action->frameCount)
    {
        if (!state->action->loop)
            return FALSE;
        nextFrame = 0;
    }

    *frameIndex = nextFrame;
    *slot = state->visibleSlot ^ 1;
    return TRUE;
}

static bool32 PresentPrepared(u8 battler, struct PmdGbaBattlerState *state, u8 frameIndex, u8 slot)
{
    const struct PmdGbaFrame *frame;

    if (!state->prepared
     || state->preparedFrameIndex != frameIndex
     || state->preparedSlot != slot
     || state->action == NULL
     || frameIndex >= state->action->frameCount)
        return FALSE;

    frame = &state->action->frames[frameIndex];
    sHost->PresentSlot(battler, slot);
    sHost->SetPresentationOffset(battler, frame->presentationX, frame->presentationY);

    state->frameIndex = frameIndex;
    state->visibleSlot = slot;
    state->ticksLeft = frame->duration > 0 ? frame->duration : 1;
    state->started = TRUE;
    state->complete = FALSE;
    ClearPrepared(state);
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

    PmdG4fCodec_Reset();
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
    PmdG4fCodec_ResetBattler(battler);
    state->action = action;
    state->active = TRUE;
    return TRUE;
}

void PmdGbaRuntime_Unbind(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return;

    /* Never write host sprite state while unbinding. The battler slot may have
     * already been replaced by a native send-out/switch sprite. */
    ClearState(&sBattlers[battler], TRUE);
    PmdG4fCodec_ResetBattler(battler);
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

u8 PmdGbaRuntime_GetFrameIndex(u8 battler)
{
    if (battler >= PMD_GBA_MAX_BATTLERS)
        return 0;
    return sBattlers[battler].frameIndex;
}

void PmdGbaRuntime_Prepare(void)
{
    u8 battler;

    if (sHost == NULL)
        return;

    for (battler = 0; battler < PMD_GBA_MAX_BATTLERS; battler++)
    {
        struct PmdGbaBattlerState *state = &sBattlers[battler];
        u8 frameIndex;
        u8 slot;
        const struct PmdGbaFrame *frame;

        if (!state->active || state->action == NULL)
            continue;

        if (!sHost->CanPresentBattler(battler))
        {
            ClearPrepared(state);
            continue;
        }

        if (!GetPendingFrame(state, &frameIndex, &slot))
        {
            ClearPrepared(state);
            continue;
        }

        if (state->prepared
         && state->preparedFrameIndex == frameIndex
         && state->preparedSlot == slot)
            continue;

        frame = &state->action->frames[frameIndex];
        ClearPrepared(state);

        /* This is the only host StageFrame call in the G4F runtime. For packed
         * frames the host invokes the tile-delta decoder here; for legacy
         * frames it invokes the existing BIOS LZ77 path here. */
        if (sHost->StageFrame(battler, slot, frame))
        {
            state->prepared = TRUE;
            state->preparedFrameIndex = frameIndex;
            state->preparedSlot = slot;
        }
    }
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
            ClearPrepared(state);
            /* Existing ownership rule: once PMD has visibly started an action,
             * native ownership abandons it completely. It never resumes a stale
             * mid-action frame when ownership returns. */
            if (state->started)
            {
                ClearState(state, FALSE);
                state->interrupted = TRUE;
                PmdG4fCodec_ResetBattler(battler);
            }
            continue;
        }

        if (!state->started)
        {
            PresentPrepared(battler, state, 0, 0);
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
                ClearPrepared(state);
                continue;
            }
            nextFrame = 0;
        }

        nextSlot = state->visibleSlot ^ 1;
        /* If Prepare could not stage this frame, hold the current visible frame
         * at ticksLeft=1 and retry next software tick. Never present stale RAM. */
        PresentPrepared(battler, state, nextFrame, nextSlot);
    }
}
