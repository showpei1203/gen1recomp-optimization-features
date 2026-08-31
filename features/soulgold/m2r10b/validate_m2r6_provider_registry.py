#!/usr/bin/env python3
from pathlib import Path
import importlib.util,tempfile,re,sys
ROOT=Path(__file__).resolve().parent
PATCHER=ROOT/'apply_m2r6_provider_registry_patch.py'
HOST=ROOT.parent/'src/m2_showdown_overlay.cpp'
spec=importlib.util.spec_from_file_location('m2r6_patcher',PATCHER)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
checks={}

# Build the same minimal sprite fixture used by the M2R5B patcher test, then
# upgrade it to the data-driven M2R6 registry.
sprite='''#include "global.h"\nEWRAM_DATA bool8 gAffineAnimsDisabled = FALSE;\nvoid BuildOamBuffer(void)\n{\n    int index=0; struct Sprite *sprite=&gSprites[index];\n    if (!sprite->inUse || sprite->invisible)\n        return;\n}\n'''
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'sprite.c'; p.write_text(sprite)
    base=mod.mod.patch_sprite(p)
    up=mod.upgrade_sprite_registry(p)
    out=p.read_text()
    checks.update({
      'base_proxy_patch': base=='patched',
      'registry_upgrade': up=='patched',
      'back_bitmap_zero_init':'gExternalShowdownProviderBack[EXTERNAL_SHOWDOWN_PROVIDER_BYTES] = {0};' in out,
      'front_bitmap_zero_init':'gExternalShowdownProviderFront[EXTERNAL_SHOWDOWN_PROVIDER_BYTES] = {0};' in out,
      'side_specific_registry':'IsOnPlayerSide(battler)' in out,
      'bitmap_lookup':'table[species >> 3]' in out and '(species & 7)' in out,
      'hardcoded_pair_removed':'species == 1289 || species == 183' not in out,
      'safe_registry_gate':'ExternalShowdown_ProviderSupported(battler, species)' in out,
      'oam_hook_retained':'ExternalShowdown_ShouldHideBattlerSprite(index)' in out,
      'registry_idempotent':mod.upgrade_sprite_registry(p)=='already',
      'provider_loss_releases_latch':'providerLost' in out and 'spriteGone || generationChanged || providerLost' in out,
    })

host=HOST.read_text()
checks.update({
 'host_write_gba':'bool write_gba' in host,
 'host_asset_scan':'scan_provider_registry()' in host,
 'host_asset_validation':'provider_asset_valid' in host,
 'host_bmp_decode_preflight':'SDL_LoadBMP(frame_path.string().c_str())' in host,
 'runtime_registry_revoke':'disable_provider_registry_entry' in host and 'native_fallback_next_frame=1' in host,
 'contract_breach_fallback':'SHOWDOWN_PROVIDER_CONTRACT_BREACH' in host,
 'host_back_front_tables':'g_provider_back' in host and 'g_provider_front' in host,
 'host_symbol_contract':'gExternalShowdownProviderBack' in host and 'gExternalShowdownProviderFront' in host,
 'host_registry_scanned_before_loop':'scan_provider_registry()' in host and host.find('scan_provider_registry()') < host.find('while (!g_quit)'),
 'host_no_prerun_ewram_commit':'install_provider_registry()' not in host,
 'host_postrun_registry_sync':'api.run();' in host and 'sync_provider_registry("post_run_shadow_sync")' in host and host.find('api.run();') < host.find('sync_provider_registry("post_run_shadow_sync")'),
 'host_shadow_verification':'actual_back' in host and 'actual_front' in host and 'shadow_verified=1' in host,
 'host_boot_zeroing_guard':'SHOWDOWN_PROVIDER_REGISTRY_DEFERRED_COMMIT' in host and 'gba_startup_ewram_zeroing' in host,
 'safe_native_fallback_log':'safe_native_fallback=1' in host,
 'registry_regression_id':'R-SD-025=1' in host or 'R-SD-026=1' in host,
 'boot_sync_regression_id':'R-SD-026=1' in host,
 'dynamic_runtime_path':'/showdown/' in host and (
     'load_showdown_clip(requested_species' in host
     and 'requested_species=display_species[battler]' in host
     and 'display_species[battler]=sprite_lab_display_species(battler,proxy.species)' in host
 ),
 'production_fallback_still_native_species':
     'disable_provider_registry_entry(proxy.species,side,"runtime_clip_load_fail")' in host,
 'sprite_lab_path_is_visual_only':
     'production_registry_mutation=0 R-SD-035=1' in host,
})
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
ok=all(checks.values())
print('M2R6_PROVIDER_REGISTRY='+('PASS' if ok else 'FAIL'))
raise SystemExit(0 if ok else 1)
