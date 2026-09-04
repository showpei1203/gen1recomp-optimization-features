#!/usr/bin/env python3
from pathlib import Path
import argparse,subprocess,sys

MAGIC = "M6X1_EXTERNAL_BRIDGE_INSTALL_V1"

BRIDGE = r'''
// M6X1 external Showdown bridge. Host registry is written by the Android frontend
// after every libretro core frame; ROM proxy state is published immediately after
// AnimateSprites and before BuildOamBuffer. All fields are u32 to keep the host ABI
// deterministic across the GBA/ARM and Android sides.
#define M6X1_ROM_MAGIC  0x4D365831u /* M6X1 */
#define M6X1_HOST_MAGIC 0x53475831u /* SGX1 */
#define M6X1_BRIDGE_VERSION 1u
#define M6X1_PROVIDER_CAPACITY 16

struct M6X1ExternalProxy
{
    u32 valid;
    u32 species;
    u32 side;
    u32 battler;
    u32 visible;
    s32 x;
    s32 y;
    s32 x2;
    s32 y2;
    u32 hFlip;
    u32 vFlip;
};

struct M6X1ExternalBridge
{
    u32 romMagic;
    u32 version;
    u32 romFrame;
    u32 hostMagic;
    u32 hostEpoch;
    u32 backCount;
    u32 frontCount;
    u32 backSpecies[M6X1_PROVIDER_CAPACITY];
    u32 frontSpecies[M6X1_PROVIDER_CAPACITY];
    struct M6X1ExternalProxy proxy[MAX_BATTLERS_COUNT];
};

EWRAM_DATA struct M6X1ExternalBridge gM6X1ExternalBridge = {0};

static bool32 M6X1_HostProvidesSpecies(u32 species, u32 side)
{
    const u32 *table;
    u32 count;
    u32 i;

    if (gM6X1ExternalBridge.hostMagic != M6X1_HOST_MAGIC)
        return FALSE;

    if (side == B_SIDE_PLAYER)
    {
        table = gM6X1ExternalBridge.backSpecies;
        count = gM6X1ExternalBridge.backCount;
    }
    else
    {
        table = gM6X1ExternalBridge.frontSpecies;
        count = gM6X1ExternalBridge.frontCount;
    }

    if (count > M6X1_PROVIDER_CAPACITY)
        count = M6X1_PROVIDER_CAPACITY;

    for (i = 0; i < count; i++)
        if (table[i] == species)
            return TRUE;

    return FALSE;
}

static void M6X1_PublishProxyAndSuppress(bool8 oldInvisible[MAX_BATTLERS_COUNT], bool8 suppressed[MAX_BATTLERS_COUNT])
{
    u32 battler;

    gM6X1ExternalBridge.romMagic = M6X1_ROM_MAGIC;
    gM6X1ExternalBridge.version = M6X1_BRIDGE_VERSION;
    gM6X1ExternalBridge.romFrame++;

    for (battler = 0; battler < MAX_BATTLERS_COUNT; battler++)
    {
        struct M6X1ExternalProxy *proxy = &gM6X1ExternalBridge.proxy[battler];
        u8 spriteId;
        struct Sprite *sprite;

        proxy->valid = FALSE;
        suppressed[battler] = FALSE;
        oldInvisible[battler] = TRUE;

        if (battler >= gBattlersCount)
            continue;

        spriteId = gBattlerSpriteIds[battler];
        if (spriteId >= MAX_SPRITES)
            continue;

        sprite = &gSprites[spriteId];
        if (!sprite->inUse)
            continue;

        oldInvisible[battler] = sprite->invisible;
        proxy->valid = TRUE;
        proxy->species = gBattleMons[battler].species;
        proxy->side = GetBattlerSide(battler);
        proxy->battler = battler;
        proxy->visible = !sprite->invisible;
        proxy->x = sprite->x;
        proxy->y = sprite->y;
        proxy->x2 = sprite->x2;
        proxy->y2 = sprite->y2;
        proxy->hFlip = sprite->hFlip;
        proxy->vFlip = sprite->vFlip;

        // Suppression is snapshot-only: hide the native OBJ for BuildOamBuffer,
        // then restore the exact native invisible bit immediately afterwards.
        // This preserves send-out/move/faint choreography and avoids poisoning
        // SoulGold's sprite state when the external provider disappears.
        if (!sprite->invisible && M6X1_HostProvidesSpecies(proxy->species, proxy->side))
        {
            sprite->invisible = TRUE;
            suppressed[battler] = TRUE;
        }
    }
}

static void M6X1_RestoreNativeVisibility(const bool8 oldInvisible[MAX_BATTLERS_COUNT], const bool8 suppressed[MAX_BATTLERS_COUNT])
{
    u32 battler;
    for (battler = 0; battler < MAX_BATTLERS_COUNT; battler++)
    {
        u8 spriteId;
        if (!suppressed[battler] || battler >= gBattlersCount)
            continue;
        spriteId = gBattlerSpriteIds[battler];
        if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
            gSprites[spriteId].invisible = oldInvisible[battler];
    }
}
'''

OLD_TICK = r'''static void RunBattleSoftwareTick(void)
{
    // Preserve the original order for every logical tick. BuildOamBuffer only
    // creates the software snapshot; the last snapshot is uploaded at VBlank.
    AnimateSprites();
    BuildOamBuffer();
    RunTextPrinters();
    UpdatePaletteFade();
    RunTasks();
}'''

NEW_TICK = r'''static void RunBattleSoftwareTick(void)
{
    bool8 m6x1OldInvisible[MAX_BATTLERS_COUNT];
    bool8 m6x1Suppressed[MAX_BATTLERS_COUNT];

    // Preserve SoulGold's native animation authority. M6X1 only mirrors the
    // resulting presentation state and removes a provider-owned native OBJ from
    // this OAM snapshot. Native sprite state is restored immediately after.
    AnimateSprites();
    M6X1_PublishProxyAndSuppress(m6x1OldInvisible, m6x1Suppressed);
    BuildOamBuffer();
    M6X1_RestoreNativeVisibility(m6x1OldInvisible, m6x1Suppressed);
    RunTextPrinters();
    UpdatePaletteFade();
    RunTasks();
}'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--soulgold', required=True)
    args = ap.parse_args()
    root = Path(args.soulgold)
    p = root / 'src' / 'battle_main.c'
    text = p.read_text()
    if MAGIC not in text:
        if OLD_TICK not in text:
            raise SystemExit('RunBattleSoftwareTick authority block not found')
        anchor = 'COMMON_DATA u8 gNumberOfMovesToChoose = 0;\n'
        if anchor not in text:
            raise SystemExit('battle global insertion anchor not found')
        bridge = '\n// ' + MAGIC + '\n' + BRIDGE + '\n'
        text = text.replace(anchor, anchor + bridge, 1)
        text = text.replace(OLD_TICK, NEW_TICK, 1)
        p.write_text(text)
    else:
        print('M6X1 bridge already installed')

    # Presentation semantics are a mandatory part of this bridge generation.
    # Do not allow a transport-only build to regress previously accepted battle
    # layering/HUD/stat behavior again.
    semantics = Path(__file__).with_name('apply_m6x1_presentation_semantics.py')
    subprocess.run([sys.executable,str(semantics),'--soulgold',str(root)],check=True)

    (root / 'M6X1_EXTERNAL_BRIDGE_INSTALL_STATUS.txt').write_text(
        'M6X1_EXTERNAL_BRIDGE_INSTALL=PASS\n'
        'bridge_symbol=gM6X1ExternalBridge\n'
        'bridge_abi=2\n'
        'proxy_hook=AFTER_ANIMATE_SPRITES_BEFORE_BUILD_OAM\n'
        'native_visibility_restore=IMMEDIATE_AFTER_BUILD_OAM\n'
        'host_registry_capacity=16\n'
        'front_provider_default=0\n'
        'presentation_semantics=M2R11E_PORT\n'
    )
    print('M6X1 external bridge + presentation semantics installed')

if __name__ == '__main__':
    main()
