#pragma once
// Resolved from pinned SoulGold ELF 671b62f421b2356961274fcb6f199d6843017f16.
// Keeping the resolved address in-branch also prevents the authority persistence
// step from carrying a dirty tracked generated_bridge.h after a successful CI build.
#define M6X1_BRIDGE_EWRAM_ADDRESS 0x02002ac8u
#define M6X1_BRIDGE_SYMBOL_NAME "gM6X1ExternalBridge"
