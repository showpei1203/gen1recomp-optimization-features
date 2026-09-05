#!/usr/bin/env python3
from pathlib import Path
import argparse

R4_JAVA_MARKER='M6X1_R4_EDGE_SAFE_STAT_MASK'
R4_ROM_MARKER='M6X1_R4_BATTLE_END_PROVIDER_LATCH'


def replace_function(text:str, signature:str, replacement:str)->str:
    start=text.find(signature)
    if start<0:
        raise SystemExit('function signature missing: '+signature)
    brace=text.find('{',start)
    if brace<0:
        raise SystemExit('function opening brace missing: '+signature)
    depth=0
    end=None
    for i in range(brace,len(text)):
        c=text[i]
        if c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0:
                end=i+1
                break
    if end is None:
        raise SystemExit('function closing brace missing: '+signature)
    return text[:start]+replacement+text[end:]


def patch_java(path:Path):
    text=path.read_text()
    if R4_JAVA_MARKER in text:
        return 'already'

    if 'M6X1_R3_NATIVE_SOULGOLD_STAT_FIDELITY' not in text:
        raise SystemExit('R3 Java authority missing before R4 patch')

    # R3 drew the stat pattern first and then used DST_IN with the Showdown frame.
    # Android saveLayer rounds fractional RectF bounds outward; pixels in that
    # rounded fringe are never touched by the bitmap source and can survive on
    # one edge. R4 reverses the Porter-Duff order: establish the exact Showdown
    # alpha destination first, then paint the full stat rectangle through SRC_IN.
    # Because the source rectangle covers the entire layer, every outside-alpha
    # pixel is explicitly driven to transparent, eliminating edge residue.
    old_ctor='statMaskPaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.DST_IN));bootPaint.setColor(Color.rgb(120,230,170));'
    new_ctor='bootPaint.setColor(Color.rgb(120,230,170));'
    if old_ctor not in text:
        raise SystemExit('R3 DST_IN ctor anchor missing')
    text=text.replace(old_ctor,new_ctor,1)

    old_comp='int layer=nc.saveLayer(dst,null);nc.drawRect(dst,statPaint);nc.drawBitmap(frame,null,dst,statMaskPaint);nc.restoreToCount(layer);'
    new_comp=(
        'int layer=nc.saveLayer(dst,null);'
        'nc.drawBitmap(frame,null,dst,statMaskPaint);'
        'statPaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.SRC_IN));'
        'nc.drawRect(dst,statPaint);'
        'statPaint.setXfermode(null);'
        'nc.restoreToCount(layer);'
        'statEdgeSafeFrames++;'
    )
    if old_comp not in text:
        raise SystemExit('R3 stat composite anchor missing')
    text=text.replace(old_comp,new_comp,1)

    old_counter='bottomUiRestoreFrames,statOverlayFrames,statNativePatternFrames,statAssetFailures,proxyGenerationChanges,proxyReleaseEvents,proxyHiddenEdges,proxyMonBgVisibleFrames;'
    new_counter='bottomUiRestoreFrames,statOverlayFrames,statNativePatternFrames,statAssetFailures,statEdgeSafeFrames,proxyGenerationChanges,proxyReleaseEvents,proxyHiddenEdges,proxyMonBgVisibleFrames;'
    if old_counter not in text:
        raise SystemExit('R3 counter anchor missing')
    text=text.replace(old_counter,new_counter,1)

    old_reset='bottomUiRestoreFrames=statOverlayFrames=statNativePatternFrames=statAssetFailures=proxyGenerationChanges=proxyReleaseEvents=proxyHiddenEdges=proxyMonBgVisibleFrames=0;'
    new_reset='bottomUiRestoreFrames=statOverlayFrames=statNativePatternFrames=statAssetFailures=statEdgeSafeFrames=proxyGenerationChanges=proxyReleaseEvents=proxyHiddenEdges=proxyMonBgVisibleFrames=0;'
    if old_reset not in text:
        raise SystemExit('R3 reset anchor missing')
    text=text.replace(old_reset,new_reset,1)

    text=text.replace('j.put("presentation_semantics","M6X1_R3_NATIVE_SOULGOLD_STAT_FIDELITY");',
                      'j.put("presentation_semantics","M6X1_R4_EDGE_TEARDOWN_GUARD");',1)

    report_anchor='j.put("stat_native_pattern_frames",gameView.statNativePatternFrames);j.put("stat_asset_failures",gameView.statAssetFailures);'
    report_repl=(report_anchor+
        'j.put("stat_mask_mode","showdown_alpha_first_src_in_full_rect");'
        'j.put("stat_edge_safe_frames",gameView.statEdgeSafeFrames);'
        'j.put("battle_end_native_flash_guard","rom_provider_ownership_latch");')
    if report_anchor not in text:
        raise SystemExit('R3 stat report anchor missing')
    text=text.replace(report_anchor,report_repl,1)

    marker_anchor='// M6X1_R3_NATIVE_SOULGOLD_STAT_FIDELITY\n'
    if marker_anchor not in text:
        raise SystemExit('R3 draw marker missing')
    text=text.replace(marker_anchor,marker_anchor+'        // '+R4_JAVA_MARKER+'\n',1)

    if 'PorterDuff.Mode.DST_IN' in text:
        raise SystemExit('R4 forbidden DST_IN stat mask survivor')
    if 'PorterDuff.Mode.SRC_IN' not in text:
        raise SystemExit('R4 SRC_IN stat mask missing')

    path.write_text(text)
    return 'patched'


def patch_rom(path:Path):
    text=path.read_text()
    if R4_ROM_MARKER in text:
        return 'already'

    bridge_anchor='EWRAM_DATA struct M6X1ExternalBridge gM6X1ExternalBridge = {0};\n'
    if bridge_anchor not in text:
        raise SystemExit('M6X1 bridge data anchor missing')
    latch='''\n// M6X1_R4_BATTLE_END_PROVIDER_LATCH\n// Battle teardown can clear gBattleMons before the old native OBJ is destroyed.\n// Keep provider ownership latched to the same sprite generation through that\n// zero-species gap, then release only when the OBJ dies, changes generation, or\n// a real nonzero replacement species appears. This prevents the native battler\n// from becoming visible for one final OAM snapshot.\nEWRAM_DATA u8 gM6X1ExternalOwnedValid[MAX_BATTLERS_COUNT] = {0};\nEWRAM_DATA u32 gM6X1ExternalOwnedSpecies[MAX_BATTLERS_COUNT] = {0};\nEWRAM_DATA u8 gM6X1ExternalOwnedSide[MAX_BATTLERS_COUNT] = {0};\nEWRAM_DATA u8 gM6X1ExternalOwnedSpriteId[MAX_BATTLERS_COUNT] = {0};\n'''
    text=text.replace(bridge_anchor,bridge_anchor+latch,1)

    publish=r'''static void M6X1_PublishProxyAndSuppress(bool8 oldInvisible[MAX_BATTLERS_COUNT], bool8 suppressed[MAX_BATTLERS_COUNT], u8 suppressedSpriteId[MAX_BATTLERS_COUNT])
{
    u32 battler;

    gM6X1ExternalBridge.romMagic = M6X1_ROM_MAGIC;
    gM6X1ExternalBridge.version = M6X1_BRIDGE_VERSION;
    gM6X1ExternalBridge.romFrame++;
    gM6X1ExternalBridge.statActive = gExternalShowdownStatAnimActive;
    gM6X1ExternalBridge.statBattler = gExternalShowdownStatAnimBattler;
    gM6X1ExternalBridge.statDecrease = gExternalShowdownStatAnimDecrease;
    gM6X1ExternalBridge.statPal = gExternalShowdownStatAnimPal;
    gM6X1ExternalBridge.statSharp = gExternalShowdownStatAnimSharp;
    gM6X1ExternalBridge.statBlend = gExternalShowdownStatAnimBlend;
    gM6X1ExternalBridge.statScroll = gExternalShowdownStatAnimScroll;

    for (battler = 0; battler < MAX_BATTLERS_COUNT; battler++)
    {
        struct M6X1ExternalProxy *proxy = &gM6X1ExternalBridge.proxy[battler];
        const bool32 activeBattler = battler < gBattlersCount;
        bool32 currentProvided = FALSE;
        bool32 latchedOwned = FALSE;
        u32 species = 0;
        u32 side = B_SIDE_PLAYER;
        u8 spriteId = 0xFF;
        struct Sprite *sprite;

        proxy->valid = FALSE;
        suppressed[battler] = FALSE;
        suppressedSpriteId[battler] = 0xFF;
        oldInvisible[battler] = TRUE;

        if (activeBattler)
        {
            spriteId = gBattlerSpriteIds[battler];
            species = gBattleMons[battler].species;
            side = GetBattlerSide(battler);
        }
        else if (gM6X1ExternalOwnedValid[battler])
        {
            spriteId = gM6X1ExternalOwnedSpriteId[battler];
            side = gM6X1ExternalOwnedSide[battler];
        }
        else
        {
            continue;
        }

        if (spriteId >= MAX_SPRITES)
        {
            gM6X1ExternalOwnedValid[battler] = FALSE;
            continue;
        }

        sprite = &gSprites[spriteId];
        if (!sprite->inUse)
        {
            gM6X1ExternalOwnedValid[battler] = FALSE;
            continue;
        }

        if (activeBattler && species != 0 && M6X1_HostProvidesSpecies(species, side))
        {
            gM6X1ExternalOwnedValid[battler] = TRUE;
            gM6X1ExternalOwnedSpecies[battler] = species;
            gM6X1ExternalOwnedSide[battler] = side;
            gM6X1ExternalOwnedSpriteId[battler] = spriteId;
            currentProvided = TRUE;
        }
        else if (gM6X1ExternalOwnedValid[battler]
              && gM6X1ExternalOwnedSpriteId[battler] == spriteId
              && (!activeBattler || species == 0)
              && M6X1_HostProvidesSpecies(gM6X1ExternalOwnedSpecies[battler], gM6X1ExternalOwnedSide[battler]))
        {
            // Teardown gap: battle data may already be zero, but this is still
            // the exact provider-owned sprite generation from the previous tick.
            species = gM6X1ExternalOwnedSpecies[battler];
            side = gM6X1ExternalOwnedSide[battler];
            latchedOwned = TRUE;
        }
        else
        {
            // A real nonzero replacement species / generation is authoritative.
            gM6X1ExternalOwnedValid[battler] = FALSE;
        }

        oldInvisible[battler] = sprite->invisible;
        proxy->valid = TRUE;
        proxy->species = species;
        proxy->side = side;
        proxy->battler = battler;
        proxy->nativeVisible = !sprite->invisible;
        proxy->monBgActive = activeBattler ? gExternalShowdownMonBgActive[battler] : FALSE;
        proxy->spriteId = spriteId;
        proxy->visible = proxy->nativeVisible || proxy->monBgActive;
        proxy->x = sprite->x;
        proxy->y = sprite->y;
        proxy->x2 = sprite->x2;
        proxy->y2 = sprite->y2;
        proxy->hFlip = sprite->hFlip;
        proxy->vFlip = sprite->vFlip;

        if (!sprite->invisible && (currentProvided || latchedOwned))
        {
            sprite->invisible = TRUE;
            suppressed[battler] = TRUE;
            suppressedSpriteId[battler] = spriteId;
        }
    }
}
'''
    text=replace_function(text,'static void M6X1_PublishProxyAndSuppress(',publish)

    restore=r'''static void M6X1_RestoreNativeVisibility(const bool8 oldInvisible[MAX_BATTLERS_COUNT], const bool8 suppressed[MAX_BATTLERS_COUNT], const u8 suppressedSpriteId[MAX_BATTLERS_COUNT])
{
    u32 battler;
    for (battler = 0; battler < MAX_BATTLERS_COUNT; battler++)
    {
        const u8 spriteId = suppressedSpriteId[battler];
        if (!suppressed[battler])
            continue;
        if (spriteId < MAX_SPRITES && gSprites[spriteId].inUse)
            gSprites[spriteId].invisible = oldInvisible[battler];
    }
}
'''
    text=replace_function(text,'static void M6X1_RestoreNativeVisibility(',restore)

    tick=r'''static void RunBattleSoftwareTick(void)
{
    bool8 m6x1OldInvisible[MAX_BATTLERS_COUNT];
    bool8 m6x1Suppressed[MAX_BATTLERS_COUNT];
    u8 m6x1SuppressedSpriteId[MAX_BATTLERS_COUNT];

    AnimateSprites();
    M6X1_PublishProxyAndSuppress(m6x1OldInvisible, m6x1Suppressed, m6x1SuppressedSpriteId);
    BuildOamBuffer();
    M6X1_RestoreNativeVisibility(m6x1OldInvisible, m6x1Suppressed, m6x1SuppressedSpriteId);
    RunTextPrinters();
    UpdatePaletteFade();
    RunTasks();
}
'''
    text=replace_function(text,'static void RunBattleSoftwareTick(void)',tick)

    if 'battler >= gBattlersCount' in text[text.find('static void M6X1_RestoreNativeVisibility('):text.find('static void RunBattleSoftwareTick(void)')]:
        raise SystemExit('R4 restore still depends on gBattlersCount')
    if 'gM6X1ExternalOwnedSpecies' not in text or 'm6x1SuppressedSpriteId' not in text:
        raise SystemExit('R4 teardown latch verification failed')

    path.write_text(text)
    return 'patched'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--framework',required=True)
    ap.add_argument('--soulgold',required=True)
    a=ap.parse_args()
    framework=Path(a.framework);soulgold=Path(a.soulgold)
    java=patch_java(framework/'android/m6x1/app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java')
    rom=patch_rom(soulgold/'src/battle_main.c')
    print('M6X1_R4_EDGE_TEARDOWN_PATCH=PASS java='+java+' rom='+rom)

if __name__=='__main__':
    main()
