#!/usr/bin/env python3
from pathlib import Path
import argparse,re

CANARY=155


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--framework',default='framework');ap.add_argument('--soulgold',default='soulgold');a=ap.parse_args()
    fw=Path(a.framework);sg=Path(a.soulgold)
    cpp=(fw/'android/m6x1/app/src/main/cpp/native_bridge.cpp').read_text()
    java=(fw/'android/m6x1/app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java').read_text()
    battle=(sg/'src/battle_main.c').read_text()
    builder=(fw/'tools/build_m6x1_showdown_pack.py').read_text()
    ondraw_start=java.find('@Override protected void onDraw(Canvas c)')
    ondraw_end=java.find('\n    }\n\n    static final class AnimFrame',ondraw_start)
    ondraw=java[ondraw_start:ondraw_end] if ondraw_start>=0 and ondraw_end>ondraw_start else ''

    checks={
      'r4_runtime_baseline_marker':'M6X1_R4_EDGE_SAFE_STAT_MASK' in java and 'M6X1_R4_BATTLE_END_PROVIDER_LATCH' in battle,
      'r4_src_in_stat_mask_sealed':'PorterDuff.Mode.SRC_IN' in java and 'PorterDuff.Mode.DST_IN' not in java,
      'r4_teardown_latch_sealed':'gM6X1ExternalOwnedSpecies' in battle and '(currentProvided || latchedOwned)' in battle,
      'bridge_v3_sealed':'kBridgeVersion=3u' in cpp and '#define M6X1_BRIDGE_VERSION 3u' in battle,
      'front_registry_vector':'M6X1_R5_FRONT_CANARY_HOST' in cpp and 'gFrontProviders' in cpp,
      'front_registry_written':'b->frontCount=(uint32_t)std::min<size_t>(gFrontProviders.size(),kProviderCapacity)' in cpp and 'b->frontSpecies[i]=gFrontProviders[i]' in cpp,
      'front_registry_readback_checked':'b->frontCount!=(uint32_t)std::min<size_t>(gFrontProviders.size(),kProviderCapacity)' in cpp,
      'front_jni_setter':'nativeSetFrontProviders' in cpp and 'nativeSetFrontProviders' in java,
      'front_proxy_jni':'nativeGetOpponentProxy' in cpp and 'nativeGetOpponentProxy' in java,
      'front_proxy_side_gate':'p.side==1&&isFrontProvider(p.species)' in cpp,
      'front_proxy_last_known_good':'nativeGetOpponentProxy' in cpp and 'gCachedBridgeValid.load(std::memory_order_acquire)' in cpp[cpp.find('nativeGetOpponentProxy'):cpp.find('nativeGetPresentationState')],
      'front_proxy_payload_14':'GetArrayLength(out)<14' in cpp[cpp.find('nativeGetOpponentProxy'):cpp.find('nativeGetPresentationState')] and 'final int[]enemyProxy=new int[14]' in java,
      'front_manifest_parser':'front_providers' in java and 'frontProviders' in java,
      'single_canary_runtime_guard':'frontProviders.size()>1' in java and 'frontProviders.containsKey(155)' in java,
      'front_rom_frame_clock':'p.frameAtRomFrame(romFrame,frontPresentationEpochRomFrame,nativeFps())' in java,
      'front_generation_identity':'frontPresentationSpriteId' in java and 'frontProxyGenerationChanges' in java,
      'front_monbg_semantics':'enemyProxy[12]' in java and 'frontProxyMonBgVisibleFrames' in java,
      'front_stat_uses_native_path':'drawStatOverlayNative(nc,frame,dst,enemyProxy[1])' in java,
      'front_draw_before_player_back':ondraw.find('drawExternalOpponentFront(nc)')>=0 and ondraw.find('drawExternalOpponentFront(nc)')<ondraw.find('if(updatePresentationProxy())'),
      'bottom_ui_after_both':ondraw.find('restoreBottomBattleUiNative(nc,bw,bh)')>ondraw.find('if(updatePresentationProxy())'),
      'front_telemetry':'external_front_overlay_frames' in java and 'external_bridge_front_count_readback' in java and 'front_canary_species' in java,
      'r5_report_marker':'M6X1_R5_FRONT_CANARY' in java,
      'builder_front_base':"FRONT_BASE='https://play.pokemonshowdown.com/sprites/ani/'" in builder,
      'builder_exact_canary':"FRONT_SPECIES = [(155,'cyndaquil',0.72)]" in builder,
      'builder_back_roster_preserved':"(1289,'sprigatito')" in builder and "(155,'cyndaquil')" in builder,
      'broad_front_rollout_blocked':not re.search(r'FRONT_SPECIES\s*=\s*\[[^\]]*,[^\]]*,',builder,re.S),
    }
    for k,v in checks.items():print(f'{k}={"PASS" if v else "FAIL"}')
    ok=all(checks.values())
    print('M6X1_R5_FRONT_CANARY_AUTHORITY='+('PASS' if ok else 'FAIL'))
    print('front_canary_species='+str(CANARY))
    print('roster_expansion_901=BLOCKED')
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
