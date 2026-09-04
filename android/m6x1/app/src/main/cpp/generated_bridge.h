#pragma once
// Resolved from pinned SoulGold ELF 671b62f421b2356961274fcb6f199d6843017f16
// after the M6X1R2 bridge ABI v3 presentation fields were added.
// Keeping the resolved address in-branch prevents the compact-authority persist
// step from carrying a dirty tracked generated_bridge.h after a successful build.
#define M6X1_BRIDGE_EWRAM_ADDRESS 0x02002ad4u
#define M6X1_BRIDGE_SYMBOL_NAME "gM6X1ExternalBridge"
