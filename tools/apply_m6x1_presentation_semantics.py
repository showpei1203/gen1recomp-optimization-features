#!/usr/bin/env python3
from pathlib import Path
import argparse,re

HUD_MARKER='M6X1_R2_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE'
STAT_MARKER='M6X1_R2_EXTERNAL_SHOWDOWN_STAT_PRESENTATION_BRIDGE'
MONBG_MARKER='M6X1_R2_EXTERNAL_SHOWDOWN_MONBG_PRESENTATION_BRIDGE'
HOST_GATE_MARKER='M6X1_R2_HOST_PROVIDER_GATE_EXPORTED'
BRIDGE_MARKER='M6X1_R2_PRESENTATION_BRIDGE_V3'


def _insert_before_in_function(text:str,func_sig:str,anchor:str,payload:str)->str:
    start=text.find(func_sig)
    if start<0: raise SystemExit('function anchor missing: '+func_sig)
    pos=text.find(anchor,start)
    if pos<0: raise SystemExit('function-local anchor missing: '+func_sig+' -> '+anchor)
    return text[:pos]+payload+text[pos:]


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

    if BRIDGE_MARKER not in text:
        version='#define M6X1_BRIDGE_VERSION 1u'
        if version not in text: raise SystemExit('M6X1 bridge version anchor missing')
        text=text.replace(version,'#define M6X1_BRIDGE_VERSION 3u /* '+BRIDGE_MARKER+' */',1)

        # R2 keeps native visibility separate from presentation visibility.
        # This is the accepted M2R5D/M3S1 semantic: monbg may hide native OAM
        # while the external body must remain visible.
        proxy_anchor='''    u32 visible;\n    s32 x;'''
        proxy_repl='''    u32 visible; /* presentation visible */\n    u32 nativeVisible;\n    u32 monBgActive;\n    u32 spriteId;\n    s32 x;'''
        if proxy_anchor not in text: raise SystemExit('M6X1 proxy visibility anchor missing')
        text=text.replace(proxy_anchor,proxy_repl,1)

        proxy_end='''    struct M6X1ExternalProxy proxy[MAX_BATTLERS_COUNT];\n};'''
        if proxy_end not in text: raise SystemExit('M6X1 bridge proxy tail anchor missing')
        stat_fields='''    struct M6X1ExternalProxy proxy[MAX_BATTLERS_COUNT];\n    u32 statActive;\n    u32 statBattler;\n    u32 statDecrease;\n    u32 statPal;\n    u32 statSharp;\n    u32 statBlend;\n    s32 statScroll;\n};'''
        text=text.replace(proxy_end,stat_fields,1)

        struct_anchor='struct M6X1ExternalBridge\n{\n'
        externs='''extern u8 gExternalShowdownStatAnimActive;\nextern u8 gExternalShowdownStatAnimBattler;\nextern u8 gExternalShowdownStatAnimDecrease;\nextern u8 gExternalShowdownStatAnimPal;\nextern u8 gExternalShowdownStatAnimSharp;\nextern u8 gExternalShowdownStatAnimBlend;\nextern s16 gExternalShowdownStatAnimScroll;\nextern u8 gExternalShowdownMonBgActive[MAX_BATTLERS_COUNT];\n\n'''
        if struct_anchor not in text: raise SystemExit('M6X1 bridge struct anchor missing')
        text=text.replace(struct_anchor,externs+struct_anchor,1)

        publish='''    gM6X1ExternalBridge.version = M6X1_BRIDGE_VERSION;\n    gM6X1ExternalBridge.romFrame++;\n'''
        if publish not in text: raise SystemExit('M6X1 bridge publish header anchor missing')
        publish2=publish+'''    gM6X1ExternalBridge.statActive = gExternalShowdownStatAnimActive;\n    gM6X1ExternalBridge.statBattler = gExternalShowdownStatAnimBattler;\n    gM6X1ExternalBridge.statDecrease = gExternalShowdownStatAnimDecrease;\n    gM6X1ExternalBridge.statPal = gExternalShowdownStatAnimPal;\n    gM6X1ExternalBridge.statSharp = gExternalShowdownStatAnimSharp;\n    gM6X1ExternalBridge.statBlend = gExternalShowdownStatAnimBlend;\n    gM6X1ExternalBridge.statScroll = gExternalShowdownStatAnimScroll;\n'''
        text=text.replace(publish,publish2,1)

        visible='''        proxy->visible = !sprite->invisible;\n        proxy->x = sprite->x;'''
        visible2='''        proxy->nativeVisible = !sprite->invisible;\n        proxy->monBgActive = gExternalShowdownMonBgActive[battler];\n        proxy->spriteId = spriteId;\n        proxy->visible = proxy->nativeVisible || proxy->monBgActive;\n        proxy->x = sprite->x;'''
        if visible not in text: raise SystemExit('M6X1 proxy visible assignment anchor missing')
        text=text.replace(visible,visible2,1)
    battle_main.write_text(text)


def patch_monbg(root:Path):
    path=root/'src'/'battle_anim.c'
    text=path.read_text()
    if MONBG_MARKER in text:
        return 'already'

    global_anchor='EWRAM_DATA static bool8 sAnimHideHpBoxes = FALSE;\n'
    if global_anchor not in text: raise SystemExit('battle_anim.c monbg global anchor missing')
    globals_block='''\n\n// M6X1_R2_EXTERNAL_SHOWDOWN_MONBG_PRESENTATION_BRIDGE\n// Final Showdown authority: monbg keeps native timing/priority semantics but\n// must not copy provider-owned native 64x64 pixels into BG1/BG2. Export the\n// presentation visibility bit so Android keeps the Showdown body alive while\n// native OAM is intentionally invisible.\nextern bool32 M6X1_HostProvidesSpecies(u32 species, u32 side);\nEWRAM_DATA u8 gExternalShowdownMonBgActive[MAX_BATTLERS_COUNT] = {0};\n'''
    text=text.replace(global_anchor,global_anchor+globals_block,1)

    clear_anchor='    gAnimFriendship = 0;\n'
    if clear_anchor not in text: raise SystemExit('ClearBattleAnimationVars anchor missing')
    text=text.replace(clear_anchor,clear_anchor+'    for (i = 0; i < MAX_BATTLERS_COUNT; i++)\n        gExternalShowdownMonBgActive[i] = FALSE;\n',1)

    move_sig='void MoveBattlerSpriteToBG(enum BattlerId battler, bool8 toBG_2, bool8 setSpriteInvisible)\n{\n'
    move_decl='    struct BattleAnimBgData animBg;\n    u8 battlerSpriteId;\n'
    move_repl=move_decl+'''    const bool32 externalShowdown = !IsContest()\n        && M6X1_HostProvidesSpecies(gBattleMons[battler].species, GetBattlerSide(battler));\n    if (externalShowdown)\n        gExternalShowdownMonBgActive[battler] = TRUE;\n'''
    start=text.find(move_sig)
    if start<0: raise SystemExit('MoveBattlerSpriteToBG signature missing')
    pos=text.find(move_decl,start)
    if pos<0: raise SystemExit('MoveBattlerSpriteToBG declaration anchor missing')
    text=text[:pos]+text[pos:].replace(move_decl,move_repl,1)

    draw1='        DrawBattlerOnBg(1, 0, 0, battlerPosition, animBg.paletteId, animBg.bgTiles, animBg.bgTilemap, animBg.tilesOffset);\n'
    draw2='        DrawBattlerOnBg(2, 0, 0, GetBattlerPosition(battler), animBg.paletteId, animBg.bgTiles + 0x1000, animBg.bgTilemap + 0x400, animBg.tilesOffset);\n'
    if draw1 not in text or draw2 not in text: raise SystemExit('DrawBattlerOnBg anchors missing')
    text=text.replace(draw1,'        if (!externalShowdown)\n'+draw1,1)
    text=text.replace(draw2,'        if (!externalShowdown)\n'+draw2,1)

    clear_payload='    gExternalShowdownMonBgActive[battler] = FALSE;\n    if (animBattlerId > 1)\n        gExternalShowdownMonBgActive[BATTLE_PARTNER(battler)] = FALSE;\n\n'
    text=_insert_before_in_function(text,'static void Cmd_clearmonbg(void)\n{','    if (sMonAnimTaskIdArray[0] != TASK_NONE)\n',clear_payload)
    text=_insert_before_in_function(text,'static void Cmd_clearmonbg_static(void)\n{','    if (IsBattlerSpriteVisible(battler))\n',clear_payload)
    path.write_text(text)
    return 'patched'


def patch_hud(root:Path):
    path=root/'src'/'battle_controller_player.c'
    text=path.read_text()
    mon_call=re.compile(r'^(?P<indent>[ \\t]*)DoBounceEffect\\(battler,\\s*BOUNCE_MON,\\s*7,\\s*1\\);[ \\t]*$',re.MULTILINE)
    found=list(mon_call.finditer(text))
    if found:
        def repl(m):
            i=m.group('indent')
            return (i+'// '+HUD_MARKER+': healthbox bounce remains native;\\n'
                    +i+'// action-selection UI must never inject y2 into external battler body.')
        text,count=mon_call.subn(repl,text)
    else:
        count=0
        if HUD_MARKER not in text and 'M6X1_R1_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE' not in text:
            raise SystemExit('BOUNCE_MON anchors missing before M6X1 HUD patch')
    if mon_call.search(text): raise SystemExit('BOUNCE_MON survivor after M6X1 HUD patch')
    if not re.search(r'DoBounceEffect\\(battler,\\s*BOUNCE_HEALTHBOX,\\s*7,\\s*1\\);',text):
        raise SystemExit('BOUNCE_HEALTHBOX disappeared unexpectedly')
    if HUD_MARKER not in text and 'M6X1_R1_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE' in text:
        text=text.replace('M6X1_R1_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE',HUD_MARKER)
    path.write_text(text)
    return count


def patch_stat(root:Path):
    path=root/'src'/'battle_anim_utility_funcs.c'
    text=path.read_text()
    if STAT_MARKER in text: return 'already'
    if 'M6X1_R1_EXTERNAL_SHOWDOWN_STAT_PRESENTATION_BRIDGE' in text:
        text=text.replace('M6X1_R1_EXTERNAL_SHOWDOWN_STAT_PRESENTATION_BRIDGE',STAT_MARKER)
        path.write_text(text)
        return 'upgraded_marker'

    include_anchor='#include "constants/songs.h"\n'
    forward='extern bool32 M6X1_HostProvidesSpecies(u32 species, u32 side);\n'
    if forward not in text:
        if include_anchor not in text: raise SystemExit('battle_anim_utility_funcs include anchor missing')
        text=text.replace(include_anchor,include_anchor+'\n// '+HOST_GATE_MARKER+'\n'+forward,1)

    global_anchor='static EWRAM_DATA struct AnimStatsChangeData *sAnimStatsChangeData = {0};\n'
    if global_anchor not in text: raise SystemExit('stat data anchor missing')
    globals_block=r'''

// M6X1_R2_EXTERNAL_SHOWDOWN_STAT_PRESENTATION_BRIDGE
// Accepted M2R4D/M2R5D semantics: stock stat animation masks native 64x64
// battler pixels into BG. Provider-owned battlers export only timing/state;
// Android applies the same presentation to the external Showdown body.
EWRAM_DATA u8 gExternalShowdownStatAnimActive = FALSE;
EWRAM_DATA u8 gExternalShowdownStatAnimBattler = 0;
EWRAM_DATA u8 gExternalShowdownStatAnimDecrease = FALSE;
EWRAM_DATA u8 gExternalShowdownStatAnimPal = 0;
EWRAM_DATA u8 gExternalShowdownStatAnimSharp = FALSE;
EWRAM_DATA u8 gExternalShowdownStatAnimBlend = 0;
EWRAM_DATA s16 gExternalShowdownStatAnimScroll = 0;
'''
    text=text.replace(global_anchor,global_anchor+globals_block,1)
    decl_anchor='static void StatsChangeAnimation_Step3(u8);\n'
    if decl_anchor not in text: raise SystemExit('stat step declaration anchor missing')
    text=text.replace(decl_anchor,decl_anchor+'static void M6X1_ExternalShowdown_StatsChangeStep(u8);\n',1)

    branch_anchor='''    if (IsContest() || (sAnimStatsChangeData->aMultipleBattlers && !IsBattlerSpriteVisible(sAnimStatsChangeData->battler2)))\n        sAnimStatsChangeData->aMultipleBattlers = FALSE;\n\n    gBattle_WIN0H = 0;\n'''
    if branch_anchor not in text: raise SystemExit('stat step1 branch anchor missing')
    branch_repl='''    if (IsContest() || (sAnimStatsChangeData->aMultipleBattlers && !IsBattlerSpriteVisible(sAnimStatsChangeData->battler2)))\n        sAnimStatsChangeData->aMultipleBattlers = FALSE;\n\n    if (!IsContest()\n     && M6X1_HostProvidesSpecies(\n            GetMonData(GetBattlerMon(sAnimStatsChangeData->battler1), MON_DATA_SPECIES),\n            GetBattlerSide(sAnimStatsChangeData->battler1)))\n    {\n        gExternalShowdownStatAnimActive = TRUE;\n        gExternalShowdownStatAnimBattler = sAnimStatsChangeData->battler1;\n        gExternalShowdownStatAnimDecrease = sAnimStatsChangeData->aDecrease;\n        gExternalShowdownStatAnimPal = sAnimStatsChangeData->aAnimStatId;\n        gExternalShowdownStatAnimSharp = sAnimStatsChangeData->aSharply;\n        gExternalShowdownStatAnimBlend = 0;\n        gExternalShowdownStatAnimScroll = 0;\n        gTasks[taskId].tVelocity = sAnimStatsChangeData->aDecrease ? -3 : 3;\n        gTasks[taskId].tTargetBlend = sAnimStatsChangeData->aSharply ? 13 : 10;\n        gTasks[taskId].tWaitTime = sAnimStatsChangeData->aSharply ? 30 : 20;\n        gTasks[taskId].tWaitTimer = 0;\n        gTasks[taskId].tFadeTimer = 0;\n        gTasks[taskId].tBlend = 0;\n        gTasks[taskId].tState = 0;\n        gTasks[taskId].func = M6X1_ExternalShowdown_StatsChangeStep;\n        if (!sAnimStatsChangeData->aDecrease)\n            PlaySE12WithPanning(SE_M_STAT_INCREASE, BattleAnimAdjustPanning2(SOUND_PAN_ATTACKER));\n        else\n            PlaySE12WithPanning(SE_M_STAT_DECREASE, BattleAnimAdjustPanning2(SOUND_PAN_ATTACKER));\n        return;\n    }\n\n    gBattle_WIN0H = 0;\n'''
    text=text.replace(branch_anchor,branch_repl,1)

    step3_anchor='static void StatsChangeAnimation_Step3(u8 taskId)\n{\n'
    if step3_anchor not in text: raise SystemExit('stat step3 implementation anchor missing')
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
    monbg=patch_monbg(root)
    hud=patch_hud(root)
    stat=patch_stat(root)
    status=root/'M6X1_PRESENTATION_SEMANTICS_STATUS.txt'
    status.write_text(
        'M6X1_PRESENTATION_SEMANTICS=PASS\n'
        'authority=M2R5D_M2R11E_M2R12G_M3S1_FINAL_PORT\n'
        'bridge_abi=3\n'
        'proxy_native_vs_presentation_visibility=SEPARATE\n'
        'monbg_external_semantic='+monbg+'\n'
        'monbg_native_pixel_copy=SUPPRESSED_FOR_PROVIDER\n'
        'hud_bounce_mon_decoupled=PASS\n'
        'hud_bounce_healthbox_preserved=PASS\n'
        'stat_external_bridge='+stat+'\n'
        'stat_provider_gate=M6X1_HostProvidesSpecies\n'
        'native_fallback_stat_path=PRESERVED\n'
        'host_raw_healthbox_abi_writes=FORBIDDEN\n'
        'hud_mon_calls_removed='+str(hud)+'\n'
    )
    print(status.read_text(),end='')

if __name__=='__main__': main()
