#pragma once
// Resolved from pinned SoulGold ELF 671b62f421b2356961274fcb6f199d6843017f16
// after the M6X1R4 provider-ownership teardown latch was added.
// The latch EWRAM allocation moves gM6X1ExternalBridge from the R3 address.
// Keeping this exact Run #14 authority in-branch prevents future builds from
// carrying a dirty generated_bridge.h during compact-authority persistence.
#define M6X1_BRIDGE_EWRAM_ADDRESS 0x02002af4u
#define M6X1_BRIDGE_SYMBOL_NAME "gM6X1ExternalBridge"
