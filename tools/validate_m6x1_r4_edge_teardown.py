#!/usr/bin/env python3
from pathlib import Path
import argparse,re


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--framework',default='framework')
    ap.add_argument('--soulgold',default='soulgold')
    a=ap.parse_args()
    fw=Path(a.framework);sg=Path(a.soulgold)
    java=(fw/'android/m6x1/app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java').read_text()
    battle=(sg/'src/battle_main.c').read_text()
    cpp=(fw/'android/m6x1/app/src/main/cpp/native_bridge.cpp').read_text()

    stat_start=java.find('private void drawStatOverlayNative(')
    stat_end=java.find('@Override protected void onDraw',stat_start)
    stat=java[stat_start:stat_end] if stat_start>=0 and stat_end>stat_start else ''
    restore_start=battle.find('static void M6X1_RestoreNativeVisibility(')
    restore_end=battle.find('static void RunBattleSoftwareTick(void)',restore_start)
    restore=battle[restore_start:restore_end] if restore_start>=0 and restore_end>restore_start else ''

    checks={
        'r4_java_marker':'M6X1_R4_EDGE_SAFE_STAT_MASK' in java,
        'r4_rom_marker':'M6X1_R4_BATTLE_END_PROVIDER_LATCH' in battle,
        'presentation_report_r4':'M6X1_R4_EDGE_TEARDOWN_GUARD' in java,

        # R3 visual content remains native SoulGold; only alpha compositing order changes.
        'r3_native_pattern_retained':'BitmapShader' in stat and 'Shader.TileMode.REPEAT' in stat,
        'r3_scroll_retained':'float bgX=decrease?64f:0f,bgY=presentation[6]' in stat and 'matrix.setTranslate(-bgX,-bgY)' in stat,
        'r3_blend_retained':'255f*blend/16f' in stat,
        'r3_assets_retained':(fw/'android/m6x1/app/src/main/assets/stat_change/manifest.json').is_file(),

        # Edge-safe alpha mask: draw exact Showdown alpha first, then cover the
        # complete layer with SRC_IN. DST_IN fringe behavior is forbidden.
        'stat_mask_alpha_first':stat.find('nc.drawBitmap(frame,null,dst,statMaskPaint)') >= 0,
        'stat_pattern_second':stat.find('nc.drawRect(dst,statPaint)') > stat.find('nc.drawBitmap(frame,null,dst,statMaskPaint)'),
        'stat_src_in':'PorterDuff.Mode.SRC_IN' in stat,
        'stat_dst_in_forbidden':'PorterDuff.Mode.DST_IN' not in java,
        'stat_xfer_reset':'statPaint.setXfermode(null)' in stat,
        'stat_edge_counter':'statEdgeSafeFrames++' in stat and 'stat_edge_safe_frames' in java,
        'old_stripes_still_forbidden':'stripe=Math.max' not in java and 'clipRect(dst.left' not in java,
        'hardcoded_tint_still_forbidden':'PorterDuffColorFilter' not in java and 'final int[][] colors=' not in java,

        # Teardown ownership remains tied to exact sprite generation and only
        # bridges zero-species/inactive gaps. A real replacement species wins.
        'owned_latch_arrays':all(x in battle for x in (
            'gM6X1ExternalOwnedValid','gM6X1ExternalOwnedSpecies','gM6X1ExternalOwnedSide','gM6X1ExternalOwnedSpriteId')),
        'teardown_zero_species_gate':'(!activeBattler || species == 0)' in battle,
        'teardown_same_generation_gate':'gM6X1ExternalOwnedSpriteId[battler] == spriteId' in battle,
        'latched_provider_revalidated':'M6X1_HostProvidesSpecies(gM6X1ExternalOwnedSpecies[battler], gM6X1ExternalOwnedSide[battler])' in battle,
        'native_snapshot_suppressed_during_latch':'(currentProvided || latchedOwned)' in battle,
        'suppressed_sprite_id_captured':'suppressedSpriteId[battler] = spriteId;' in battle,
        'restore_uses_captured_sprite_id':'const u8 spriteId = suppressedSpriteId[battler];' in restore,
        'restore_not_gbattlerscount_gated':'battler >= gBattlersCount' not in restore,
        'tick_passes_sprite_generation':'m6x1SuppressedSpriteId' in battle,

        # Sealed R2/R3 baseline must remain intact.
        'bridge_v3':'kBridgeVersion=3u' in cpp and '#define M6X1_BRIDGE_VERSION 3u' in battle,
        'last_known_good_snapshot':'gCachedBridgeValid' in cpp,
        'rom_frame_clock':'frameAtRomFrame' in java,
        'front_still_blocked':'b->frontCount=0;' in cpp,
        'x2_y2_retained':'proxy->x2 = sprite->x2;' in battle and 'proxy->y2 = sprite->y2;' in battle,
    }

    for k,v in checks.items():
        print(f'{k}={"PASS" if v else "FAIL"}')
    ok=all(checks.values())
    print('M6X1_R4_EDGE_TEARDOWN_AUTHORITY='+('PASS' if ok else 'FAIL'))
    return 0 if ok else 1

if __name__=='__main__':
    raise SystemExit(main())
