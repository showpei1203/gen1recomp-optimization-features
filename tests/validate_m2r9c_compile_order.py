#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
src=(ROOT/'src/m2_showdown_overlay.cpp').read_text(encoding='utf-8')

def pos(token):
    p=src.find(token)
    if p < 0:
        raise SystemExit(f'M2R9C_FAIL=TOKEN_MISSING:{token}')
    return p

display_decl=pos('std::array<uint16_t,kExternalBattlers> requested_species{};')
ready_decl=pos('std::array<bool,kExternalBattlers> provider_ready{};')
telemetry=pos('SPRITE_LAB_RUNTIME frame=')
any_proxy=pos('const bool any_proxy_valid=std::any_of')
checks={
    'requested_species_decl_before_runtime': display_decl < telemetry,
    'provider_ready_decl_before_runtime': ready_decl < telemetry,
    'any_proxy_valid_before_runtime': any_proxy < telemetry,
    'runtime_uses_requested_species': 'player_display=" << requested_species[0]' in src and 'opponent_display=" << requested_species[1]' in src,
    'runtime_uses_provider_ready': 'player_ready=" << (provider_ready[0]?1:0)' in src and 'opponent_ready=" << (provider_ready[1]?1:0)' in src,
    'runtime_not_teardown_edge_only': 'g_sprite_lab_enabled && (battle || any_proxy_valid) && (g_frame%30u)==0u' in src,
    'regression_id': 'R-SD-036=1' in src,
}
for k,v in checks.items():
    print(f'{k}={"PASS" if v else "FAIL"}')
ok=all(checks.values())
print('M2R9C_COMPILE_ORDER_STATIC='+('PASS' if ok else 'FAIL'))
raise SystemExit(0 if ok else 1)
