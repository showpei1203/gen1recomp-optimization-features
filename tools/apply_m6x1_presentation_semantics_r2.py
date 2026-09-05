#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util,re,subprocess,sys

HUD_MARKER='M6X1_R2_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE'


def load_base():
    p=Path(__file__).with_name('apply_m6x1_presentation_semantics.py')
    spec=importlib.util.spec_from_file_location('m6x1_r2_semantics_base',p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def patch_hud(root:Path):
    """Exact accepted M2/R1 BOUNCE_MON patch, retained as permanent R4 authority."""
    path=root/'src'/'battle_controller_player.c'
    text=path.read_text()
    mon_call=re.compile(r'^(?P<indent>[ \t]*)DoBounceEffect\(battler,\s*BOUNCE_MON,\s*7,\s*1\);[ \t]*$',re.MULTILINE)
    found=list(mon_call.finditer(text))
    if found:
        def repl(m):
            i=m.group('indent')
            return (i+'// '+HUD_MARKER+': healthbox bounce remains native;\n'
                    +i+'// action-selection UI must never inject y2 into external battler body.')
        text,count=mon_call.subn(repl,text)
    else:
        count=0
        if HUD_MARKER not in text and 'M6X1_R1_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE' not in text:
            raise SystemExit('BOUNCE_MON anchors missing before M6X1 R4 HUD patch')
    if mon_call.search(text):
        raise SystemExit('BOUNCE_MON survivor after M6X1 R4 HUD patch')
    if not re.search(r'DoBounceEffect\(battler,\s*BOUNCE_HEALTHBOX,\s*7,\s*1\);',text):
        raise SystemExit('BOUNCE_HEALTHBOX disappeared unexpectedly')
    if HUD_MARKER not in text and 'M6X1_R1_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE' in text:
        text=text.replace('M6X1_R1_EXTERNAL_SHOWDOWN_HUD_BOUNCE_DECOUPLE',HUD_MARKER)
    path.write_text(text)
    return count


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--soulgold',required=True);a=ap.parse_args()
    root=Path(a.soulgold);base=load_base()
    base.patch_host_gate(root)
    monbg=base.patch_monbg(root)
    hud=patch_hud(root)
    stat=base.patch_stat(root)

    framework=Path(__file__).resolve().parents[1]

    # R3 native SoulGold stat textures remain the visual authority.
    prep=Path(__file__).with_name('prepare_m6x1_native_stat_assets.py')
    subprocess.run([
        sys.executable,str(prep),'--soulgold',str(root),
        '--android-root',str(framework/'android'/'m6x1')
    ],check=True)

    # R4 is sealed physical-device authority. Use the declaration-safe runner.
    r4=Path(__file__).with_name('apply_m6x1_r4_edge_teardown_patch_v2.py')
    subprocess.run([
        sys.executable,str(r4),'--framework',str(framework),'--soulgold',str(root)
    ],check=True)

    # R5 opens exactly one opponent FRONT provider after R4. ROM provider
    # ownership is already side-generic, so R5 changes host registry/compositor
    # only and keeps 901/broad FRONT rollout blocked.
    r5=Path(__file__).with_name('apply_m6x1_r5_front_canary.py')
    subprocess.run([
        sys.executable,str(r5),'--framework',str(framework),'--soulgold',str(root)
    ],check=True)
    r5v=Path(__file__).with_name('validate_m6x1_r5_front_canary.py')
    subprocess.run([
        sys.executable,str(r5v),'--framework',str(framework),'--soulgold',str(root)
    ],check=True)

    status=root/'M6X1_PRESENTATION_SEMANTICS_STATUS.txt'
    status.write_text(
        'M6X1_PRESENTATION_SEMANTICS=PASS\n'
        'authority=M2R5D_M2R11E_M2R12G_M3S1_PLUS_R3_NATIVE_STAT_PLUS_R4_EDGE_TEARDOWN_PLUS_R5_FRONT_CANARY\n'
        'bridge_abi=3\n'
        'proxy_native_vs_presentation_visibility=SEPARATE\n'
        'monbg_external_semantic='+monbg+'\n'
        'monbg_native_pixel_copy=SUPPRESSED_FOR_PROVIDER\n'
        'hud_bounce_mon_decoupled=PASS\n'
        'hud_bounce_healthbox_preserved=PASS\n'
        'stat_external_bridge='+stat+'\n'
        'stat_provider_gate=M6X1_HostProvidesSpecies\n'
        'stat_render=PINNED_SOULGOLD_TILEMAP_PALETTE_SCROLL_SHOWDOWN_ALPHA_MASK\n'
        'stat_mask_order=SHOWDOWN_ALPHA_FIRST_THEN_SRC_IN_FULL_PATTERN_RECT\n'
        'stat_edge_residue_guard=PASS\n'
        'battle_end_provider_ownership_latch=PASS\n'
        'battle_end_native_flash_guard=PASS\n'
        'function_patch_boundary=FORWARD_DECLARATION_SAFE\n'
        'front_rollout=R5_SINGLE_SPECIES_CANARY\n'
        'front_canary_species=155\n'
        'front_canary_name=cyndaquil\n'
        'roster_expansion_901=BLOCKED\n'
        'legacy_stripe_tint_approximation=FORBIDDEN\n'
        'native_fallback_stat_path=PRESERVED\n'
        'host_raw_healthbox_abi_writes=FORBIDDEN\n'
        'hud_mon_calls_removed='+str(hud)+'\n'
    )
    print(status.read_text(),end='')

if __name__=='__main__':main()
