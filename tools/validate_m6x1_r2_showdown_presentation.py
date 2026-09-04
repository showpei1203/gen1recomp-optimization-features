#!/usr/bin/env python3
from pathlib import Path
import argparse,re


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--framework',default='framework')
    ap.add_argument('--soulgold',default='soulgold')
    a=ap.parse_args()
    fw=Path(a.framework); sg=Path(a.soulgold)
    java=(fw/'android/m6x1/app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java').read_text()
    cpp=(fw/'android/m6x1/app/src/main/cpp/native_bridge.cpp').read_text()
    battle=(sg/'src/battle_main.c').read_text()
    anim=(sg/'src/battle_anim.c').read_text()
    stat=(sg/'src/battle_anim_utility_funcs.c').read_text()
    player=(sg/'src/battle_controller_player.c').read_text()
    assets=fw/'android/m6x1/app/src/main/assets/stat_change'
    expected=[f'{d}_{p}.png' for d in ('increase','decrease') for p in
              ('attack','defense','accuracy','speed','evasion','sp_attack','sp_defense','multiple')]

    checks={
        # Permanent M2/M3 presentation rules.
        'bridge_v3':'#define M6X1_BRIDGE_VERSION 3u' in battle and 'kBridgeVersion=3u' in cpp,
        'native_vs_presentation_visibility':'nativeVisible' in battle and 'monBgActive' in battle and 'proxy->visible = proxy->nativeVisible || proxy->monBgActive;' in battle,
        'sprite_generation_identity':'spriteId' in battle and 'presentationSpriteId' in java and 'proxyGenerationChanges' in java,
        'monbg_semantic_export':'M6X1_R2_EXTERNAL_SHOWDOWN_MONBG_PRESENTATION_BRIDGE' in anim and 'gExternalShowdownMonBgActive' in anim,
        'monbg_native_pixels_suppressed':'if (!externalShowdown)' in anim and 'DrawBattlerOnBg' in anim,
        'stat_native_pixels_bypassed':'M6X1_R2_EXTERNAL_SHOWDOWN_STAT_PRESENTATION_BRIDGE' in stat and 'M6X1_ExternalShowdown_StatsChangeStep' in stat,
        'hud_mon_bounce_removed':not re.search(r'DoBounceEffect\(battler,\s*BOUNCE_MON,\s*7,\s*1\);',player),
        'hud_healthbox_bounce_retained':bool(re.search(r'DoBounceEffect\(battler,\s*BOUNCE_HEALTHBOX,\s*7,\s*1\);',player)),
        'x2_y2_retained':'proxy->x2 = sprite->x2;' in battle and 'proxy->y2 = sprite->y2;' in battle and 'proxy[2]+proxy[4]' in java and 'proxy[3]+proxy[5]' in java,

        'last_known_good_snapshot':'gCachedBridgeValid' in cpp and 'M6X1_R2_LAST_KNOWN_GOOD_SNAPSHOT' in cpp,
        'getter_not_transient_fresh_gated':'nativeGetPlayerProxy' in cpp and '!gCachedBridgeValid.load' in cpp and '!gBridgeFresh.load' not in cpp[cpp.find('nativeGetPlayerProxy'):cpp.find('nativeDrainAudio')],
        'proxy_payload_14':'GetArrayLength(out)<14' in cpp and 'final int[]proxy=new int[14]' in java,
        'rom_frame_animation_clock':'frameAtRomFrame' in java and 'provider_animation_clock","rom_frame' in java,
        'no_android_wallclock_provider':'frameAt(SystemClock.uptimeMillis())' not in java,
        'first_visible_epoch':'presentationVisibleOnce' in java and 'presentationEpochRomFrame=romFrame' in java,
        'provider_release_on_gap':'proxyReleaseEvents' in java and 'resetPresentationProxy()' in java,

        # R3: exact pinned SoulGold stat-change art semantics. The old accepted
        # M2 approximation is now explicitly forbidden after AYN THOR rejected it.
        'r3_marker':'M6X1_R3_NATIVE_SOULGOLD_STAT_FIDELITY' in java,
        'native_stat_assets_complete':assets.is_dir() and (assets/'manifest.json').is_file() and all((assets/x).is_file() for x in expected),
        'native_stat_pattern_shader':'BitmapShader' in java and 'Shader.TileMode.REPEAT' in java,
        'showdown_alpha_mask':'PorterDuff.Mode.DST_IN' in java and 'statMaskPaint' in java,
        'native_scroll_authority':'float bgX=decrease?64f:0f,bgY=presentation[6]' in java and 'matrix.setTranslate(-bgX,-bgY)' in java,
        'native_blend_authority':'255f*blend/16f' in java,
        'old_stat_stripes_forbidden':'stripe=Math.max' not in java and 'clipRect(dst.left' not in java,
        'old_hardcoded_tint_forbidden':'PorterDuffColorFilter' not in java and 'final int[][] colors=' not in java,
        'native_resolution_composite':'Bitmap bmp,compositeBmp' in java and 'Canvas nc=new Canvas(compositeBmp)' in java,
        'stat_same_frame_geometry':'drawStatOverlayNative(nc,frame,dst,proxy[1])' in java,
        'stat_before_final_scale':java.find('drawStatOverlayNative(nc,frame,dst,proxy[1])') < java.find('c.drawBitmap(compositeBmp'),
        'bottom_ui_after_battler':java.find('restoreBottomBattleUiNative(nc,bw,bh)') > java.find('drawStatOverlayNative(nc,frame,dst,proxy[1])'),

        'no_host_healthbox_stride_guess':'BattleHealthboxInfo' not in cpp and 'kBattleHealthboxInfoSize' not in cpp,
        'front_rollout_still_blocked':'b->frontCount=0;' in cpp,
    }
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    ok=all(checks.values())
    print('M6X1_R3_SHOWDOWN_PRESENTATION_AUTHORITY='+('PASS' if ok else 'FAIL'))
    return 0 if ok else 1

if __name__=='__main__':
    raise SystemExit(main())
