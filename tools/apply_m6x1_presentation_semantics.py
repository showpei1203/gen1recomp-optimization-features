#!/usr/bin/env python3
from pathlib import Path
import argparse,re

HUD_MARKER='M6X1_R1_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE'
STAT_MARKER='M6X1_R1_EXTERNAL_SHOWDOWN_STAT_PRESENTATION_BRIDGE'
HOST_GATE_MARKER='M6X1_R1_HOST_PROVIDER_GATE_EXPORTED'


def patch_host_gate(root:Path):
    battle_main=root/'src'/'battle_main.c'
    text=battle_main.read_text()
    old='static bool32 M6X1_HostProvidesSpecies(u32 species, u32 side)'
    new='bool32 M6X1_HostProvidesSpecies(u32 species, u32 side)'
    if old in text:
        text=text.replace(old,new,1)
    elif new not in text:
        raise SystemExit('M6X1 host provider gate not found in battle_main.c')
    if HOST_GATE_MARKER not in text:
        text=text.replace(new,'// '+HOST_GATE_MARKER+'\n'+new,1)
    battle_main.write_text(text)

    header=root/'include'/'battle.h'
    h=header.read_text()
    decl='bool32 M6X1_HostProvidesSpecies(u32 species, u32 side);'
    if decl not in h:
        anchor='void RunBattleScriptCommands(void);\n'
        if anchor not in h:
            raise SystemExit('battle.h declaration anchor missing')
        h=h.replace(anchor,anchor+'\n// '+HOST_GATE_MARKER+'\n'+decl+'\n',1)
        header.write_text(h)


def patch_hud(root:Path):
    path=root/'src'/'battle_controller_player.c'
    text=path.read_text()
    mon_call=re.compile(r'^(?P<indent>[ \t]*)DoBounceEffect\(battler,\s*BOUNCE_MON,\s*7,\s*1\);[ \t]*$',re.MULTILINE)
    found=list(mon_call.finditer(text))
    if found:
        def repl(m):
            i=m.group('indent')
            return (i+'// '+HUD_MARKER+': healthbox bounce remains native;\n'
                    +i+'// external battler body must not inherit action-menu HUD y2 bounce.')
        text,count=mon_call.subn(repl,text)
    else:
        count=0
        if HUD_MARKER not in text:
            raise SystemExit('BOUNCE_MON anchors missing before M6X1 HUD patch')
    if mon_call.search(text):
        raise SystemExit('BOUNCE_MON survivor after M6X1 HUD patch')
    if not re.search(r'DoBounceEffect\(battler,\s*BOUNCE_HEALTHBOX,\s*7,\s*1\);',text):
        raise SystemExit('BOUNCE_HEALTHBOX disappeared unexpectedly')
    path.write_text(text)
    return count


def patch_stat(root:Path):
    path=root/'src'/'battle_anim_utility_funcs.c'
    text=path.read_text()
    if STAT_MARKER in text:
        return 'already'

    global_anchor='static EWRAM_DATA struct AnimStatsChangeData *sAnimStatsChangeData = {0};\n'
    if global_anchor not in text:
        raise SystemExit('stat data anchor missing')
    globals_block=r'''

// M6X1_R1_EXTERNAL_SHOWDOWN_STAT_PRESENTATION_BRIDGE
// Ported from the accepted M2R4D/M2R11E semantics. The stock stat animation
// masks a native 64x64 battler copy into BG1. For provider-owned external
// battlers, export the timing/state and let Android apply it to Showdown.
EWRAM_DATA u8 gExternalShowdownStatAnimActive = FALSE;
EWRAM_DATA u8 gExternalShowdownStatAnimBattler = 0xFF;
EWRAM_DATA u8 gExternalShowdownStatAnimDecrease = FALSE;
EWRAM_DATA u8 gExternalShowdownStatAnimPal = 0;
EWRAM_DATA u8 gExternalShowdownStatAnimSharp = FALSE;
EWRAM_DATA u8 gExternalShowdownStatAnimBlend = 0;
EWRAM_DATA s16 gExternalShowdownStatAnimScroll = 0;
'''
    text=text.replace(global_anchor,global_anchor+globals_block,1)

    decl_anchor='static void StatsChangeAnimation_Step3(u8);\n'
    if decl_anchor not in text:
        raise SystemExit('stat step declaration anchor missing')
    text=text.replace(decl_anchor,decl_anchor+'static void M6X1_ExternalShowdown_StatsChangeStep(u8);\n',1)

    branch_anchor='''    if (IsContest() || (sAnimStatsChangeData->aMultipleBattlers && !IsBattlerSpriteVisible(sAnimStatsChangeData->battler2)))
        sAnimStatsChangeData->aMultipleBattlers = FALSE;

    gBattle_WIN0H = 0;
'''
    if branch_anchor not in text:
        raise SystemExit('stat step1 branch anchor missing')
    branch_repl='''    if (IsContest() || (sAnimStatsChangeData->aMultipleBattlers && !IsBattlerSpriteVisible(sAnimStatsChangeData->battler2)))
        sAnimStatsChangeData->aMultipleBattlers = FALSE;

    // Only provider-owned player battlers take the external path. Native
    // fallback must retain the stock animation unchanged.
    if (!IsContest()
     && IsOnPlayerSide(sAnimStatsChangeData->battler1)
     && M6X1_HostProvidesSpecies(gBattleMons[sAnimStatsChangeData->battler1].species, B_SIDE_PLAYER))
    {
        gExternalShowdownStatAnimActive = TRUE;
        gExternalShowdownStatAnimBattler = sAnimStatsChangeData->battler1;
        gExternalShowdownStatAnimDecrease = sAnimStatsChangeData->aDecrease;
        gExternalShowdownStatAnimPal = sAnimStatsChangeData->aAnimStatId;
        gExternalShowdownStatAnimSharp = sAnimStatsChangeData->aSharply;
        gExternalShowdownStatAnimBlend = 0;
        gExternalShowdownStatAnimScroll = 0;
        gTasks[taskId].tVelocity = sAnimStatsChangeData->aDecrease ? -3 : 3;
        gTasks[taskId].tTargetBlend = sAnimStatsChangeData->aSharply ? 13 : 10;
        gTasks[taskId].tWaitTime = sAnimStatsChangeData->aSharply ? 30 : 20;
        gTasks[taskId].tWaitTimer = 0;
        gTasks[taskId].tFadeTimer = 0;
        gTasks[taskId].tBlend = 0;
        gTasks[taskId].tState = 0;
        gTasks[taskId].func = M6X1_ExternalShowdown_StatsChangeStep;
        if (!sAnimStatsChangeData->aDecrease)
            PlaySE12WithPanning(SE_M_STAT_INCREASE, BattleAnimAdjustPanning2(SOUND_PAN_ATTACKER));
        else
            PlaySE12WithPanning(SE_M_STAT_DECREASE, BattleAnimAdjustPanning2(SOUND_PAN_ATTACKER));
        return;
    }

    gBattle_WIN0H = 0;
'''
    text=text.replace(branch_anchor,branch_repl,1)

    step3_anchor='static void StatsChangeAnimation_Step3(u8 taskId)\n{\n'
    if step3_anchor not in text:
        raise SystemExit('stat step3 implementation anchor missing')
    external_impl=r'''static void M6X1_ExternalShowdown_StatsChangeStep(u8 taskId)
{
    gExternalShowdownStatAnimScroll += gTasks[taskId].tVelocity;

    switch (gTasks[taskId].tState)
    {
    case 0:
        if (gTasks[taskId].tFadeTimer++ > 0)
        {
            gTasks[taskId].tFadeTimer = 0;
            gTasks[taskId].tBlend++;
            gExternalShowdownStatAnimBlend = gTasks[taskId].tBlend;
            if (gTasks[taskId].tBlend == gTasks[taskId].tTargetBlend)
                gTasks[taskId].tState++;
        }
        break;
    case 1:
        if (++gTasks[taskId].tWaitTimer == gTasks[taskId].tWaitTime)
            gTasks[taskId].tState++;
        break;
    case 2:
        if (gTasks[taskId].tFadeTimer++ > 0)
        {
            gTasks[taskId].tFadeTimer = 0;
            gTasks[taskId].tBlend--;
            gExternalShowdownStatAnimBlend = gTasks[taskId].tBlend;
            if (gTasks[taskId].tBlend == 0)
                gTasks[taskId].tState++;
        }
        break;
    case 3:
        gExternalShowdownStatAnimActive = FALSE;
        gExternalShowdownStatAnimBattler = 0xFF;
        gExternalShowdownStatAnimBlend = 0;
        gExternalShowdownStatAnimScroll = 0;
        FREE_AND_SET_NULL(sAnimStatsChangeData);
        DestroyAnimVisualTask(taskId);
        break;
    }
}

'''
    text=text.replace(step3_anchor,external_impl+step3_anchor,1)
    path.write_text(text)
    return 'patched'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--soulgold',required=True);a=ap.parse_args()
    root=Path(a.soulgold)
    patch_host_gate(root)
    hud=patch_hud(root)
    stat=patch_stat(root)
    status=root/'M6X1_PRESENTATION_SEMANTICS_STATUS.txt'
    status.write_text(
        'M6X1_PRESENTATION_SEMANTICS=PASS\n'
        'authority=M2R11E_PORT\n'
        'hud_bounce_mon_decoupled=PASS\n'
        'hud_bounce_healthbox_preserved=PASS\n'
        'stat_external_bridge='+stat+'\n'
        'stat_provider_gate=M6X1_HostProvidesSpecies\n'
        'native_fallback_stat_path=PRESERVED\n'
        'hud_mon_calls_removed='+str(hud)+'\n'
    )
    print(status.read_text(),end='')

if __name__=='__main__': main()
