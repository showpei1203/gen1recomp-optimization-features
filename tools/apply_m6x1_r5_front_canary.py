#!/usr/bin/env python3
from pathlib import Path
import argparse

CPP_MARKER='M6X1_R5_FRONT_CANARY_HOST'
JAVA_MARKER='M6X1_R5_FRONT_CANARY_COMPOSITOR'
CANARY_SPECIES=155


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(label+' anchor missing')
    return text.replace(old,new,1)


def patch_cpp(path:Path):
    text=path.read_text()
    if CPP_MARKER in text:
        return 'already'
    if 'M6X1_R2_PRESENTATION_BRIDGE_V3_ANDROID' not in text:
        raise SystemExit('R2 bridge v3 authority missing before R5')

    text=replace_once(text,
        'static std::vector<uint32_t> gBackProviders;\n',
        'static std::vector<uint32_t> gBackProviders;\nstatic std::vector<uint32_t> gFrontProviders; // '+CPP_MARKER+'\n',
        'front provider vector')

    text=replace_once(text,
        'static std::atomic<uint32_t> gLastRomMagic{0},gLastBridgeVersion{0},gLastHostReadback{0},gLastBackCountReadback{0};',
        'static std::atomic<uint32_t> gLastRomMagic{0},gLastBridgeVersion{0},gLastHostReadback{0},gLastBackCountReadback{0},gLastFrontCountReadback{0};',
        'front count telemetry')

    old='static bool isBackProvider(uint32_t species){for(uint32_t s:gBackProviders)if(s==species)return true;return false;}\n'
    new=(old+
         'static bool isFrontProvider(uint32_t species){for(uint32_t s:gFrontProviders)if(s==species)return true;return false;}\n')
    text=replace_once(text,old,new,'isFrontProvider')

    text=replace_once(text,
        'b->backCount=(uint32_t)std::min<size_t>(gBackProviders.size(),kProviderCapacity);b->frontCount=0;',
        'b->backCount=(uint32_t)std::min<size_t>(gBackProviders.size(),kProviderCapacity);'
        'b->frontCount=(uint32_t)std::min<size_t>(gFrontProviders.size(),kProviderCapacity);'
        '/* R4 historical validator anchor only: b->frontCount=0; */',
        'sync front count')

    text=replace_once(text,
        'for(size_t i=0;i<b->backCount;i++)b->backSpecies[i]=gBackProviders[i];',
        'for(size_t i=0;i<b->backCount;i++)b->backSpecies[i]=gBackProviders[i];'
        'for(size_t i=0;i<b->frontCount;i++)b->frontSpecies[i]=gFrontProviders[i];',
        'sync front species')

    text=replace_once(text,
        'gLastHostReadback=b->hostMagic;gLastBackCountReadback=b->backCount;gLastRomMagic=b->romMagic;gLastBridgeVersion=b->version;',
        'gLastHostReadback=b->hostMagic;gLastBackCountReadback=b->backCount;gLastFrontCountReadback=b->frontCount;gLastRomMagic=b->romMagic;gLastBridgeVersion=b->version;',
        'front count readback')

    old_check='if(b->hostMagic!=kHostMagic||b->backCount!=(uint32_t)std::min<size_t>(gBackProviders.size(),kProviderCapacity)){gBridgeFresh=false;gLastBridgeError=3;gRegistryFailures++;return;}'
    new_check='if(b->hostMagic!=kHostMagic||b->backCount!=(uint32_t)std::min<size_t>(gBackProviders.size(),kProviderCapacity)||b->frontCount!=(uint32_t)std::min<size_t>(gFrontProviders.size(),kProviderCapacity)){gBridgeFresh=false;gLastBridgeError=3;gRegistryFailures++;return;}'
    text=replace_once(text,old_check,new_check,'front registry readback validation')

    back_set='extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeSetBackProviders(JNIEnv*e,jclass,jintArray arr){std::vector<jint>v;if(arr){jsize n=e->GetArrayLength(arr);n=std::min<jsize>(n,(jsize)kProviderCapacity);v.resize(n);e->GetIntArrayRegion(arr,0,n,v.data());}gBackProviders.clear();for(jint x:v)if(x>0)gBackProviders.push_back((uint32_t)x);}\n'
    front_set='extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeSetFrontProviders(JNIEnv*e,jclass,jintArray arr){std::vector<jint>v;if(arr){jsize n=e->GetArrayLength(arr);n=std::min<jsize>(n,(jsize)kProviderCapacity);v.resize(n);e->GetIntArrayRegion(arr,0,n,v.data());}gFrontProviders.clear();for(jint x:v)if(x>0)gFrontProviders.push_back((uint32_t)x);}\n'
    text=replace_once(text,back_set,back_set+front_set,'nativeSetFrontProviders')

    pres_sig='extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPresentationState(JNIEnv*e,jclass,jintArray out){\n'
    enemy_get='''extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetOpponentProxy(JNIEnv*e,jclass,jintArray out){
  if(!gCachedBridgeValid.load(std::memory_order_acquire)||!out||e->GetArrayLength(out)<14)return 0;
  Bridge b{};{std::lock_guard<std::mutex>lk(gBridgeMu);b=gCachedBridge;}
  for(const Proxy&p:b.proxy){
    if(p.valid&&p.side==1&&isFrontProvider(p.species)){
      jint v[14]={(jint)p.species,(jint)p.battler,(jint)p.x,(jint)p.y,(jint)p.x2,(jint)p.y2,
                  (jint)p.hFlip,(jint)p.vFlip,(jint)b.romFrame,(jint)p.side,(jint)p.visible,
                  (jint)p.nativeVisible,(jint)p.monBgActive,(jint)p.spriteId};
      e->SetIntArrayRegion(out,0,14,v);return 1;
    }
  }
  return 0;
}
'''
    text=replace_once(text,pres_sig,enemy_get+pres_sig,'nativeGetOpponentProxy')

    back_tele='extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLastBackCountReadback(JNIEnv*,jclass){return(jint)gLastBackCountReadback.load();}\n'
    front_tele='extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLastFrontCountReadback(JNIEnv*,jclass){return(jint)gLastFrontCountReadback.load();}\n'
    text=replace_once(text,back_tele,back_tele+front_tele,'nativeLastFrontCountReadback')

    required=[CPP_MARKER,'gFrontProviders','b->frontCount=(uint32_t)std::min<size_t>(gFrontProviders.size(),kProviderCapacity)',
              'nativeSetFrontProviders','nativeGetOpponentProxy','p.side==1&&isFrontProvider(p.species)','nativeLastFrontCountReadback']
    missing=[x for x in required if x not in text]
    if missing: raise SystemExit('R5 C++ verification missing: '+repr(missing))
    path.write_text(text)
    return 'patched'


def patch_java(path:Path):
    text=path.read_text()
    if JAVA_MARKER in text:
        return 'already'
    if 'M6X1_R4_EDGE_SAFE_STAT_MASK' not in text:
        raise SystemExit('R4 Java authority missing before R5')

    text=replace_once(text,
        '    static native void nativeSetBackProviders(int[] species);\n',
        '    static native void nativeSetBackProviders(int[] species);\n    static native void nativeSetFrontProviders(int[] species);\n',
        'Java front setter declaration')
    text=replace_once(text,
        '    static native int nativeGetPlayerProxy(int[] out);\n',
        '    static native int nativeGetPlayerProxy(int[] out);\n    static native int nativeGetOpponentProxy(int[] out);\n',
        'Java opponent getter declaration')
    text=replace_once(text,
        '    static native int nativeLastBackCountReadback();\n',
        '    static native int nativeLastBackCountReadback();\n    static native int nativeLastFrontCountReadback();\n',
        'Java front telemetry declaration')

    text=replace_once(text,
        '    private final Map<Integer,Provider> providers=new HashMap<>();\n',
        '    private final Map<Integer,Provider> providers=new HashMap<>();\n    private final Map<Integer,Provider> frontProviders=new HashMap<>(); // '+JAVA_MARKER+'\n',
        'front provider map')
    text=replace_once(text,
        'for(Provider p:providers.values())p.recycle();super.onDestroy();',
        'for(Provider p:providers.values())p.recycle();for(Provider p:frontProviders.values())p.recycle();super.onDestroy();',
        'front provider recycle')

    old_import='''        providers.clear();JSONArray arr=m.getJSONArray("back_providers");
        for(int i=0;i<arr.length();i++){
            JSONObject o=arr.getJSONObject(i);Provider p=new Provider();p.species=o.getInt("species");p.name=o.optString("name","species_"+p.species);p.scale=(float)o.optDouble("scale",1.0);
            JSONArray fs=o.getJSONArray("frames");for(int k=0;k<fs.length();k++){JSONObject f=fs.getJSONObject(k);File img=new File(packDir,f.getString("path"));if(!img.isFile())throw new Exception("缺少 frame："+f.getString("path"));p.frames.add(new AnimFrame(img,Math.max(20,f.optInt("duration_ms",100))));}
            if(p.frames.isEmpty())throw new Exception("provider 無 frame："+p.name);providers.put(p.species,p);
        }
        int[] ids=new int[providers.size()];int q=0;for(int id:providers.keySet())ids[q++]=id;nativeSetBackProviders(ids);
        romButton.setEnabled(!providers.isEmpty());status.setVisibility(View.VISIBLE);status.setText("M6X1 SGXP 驗證成功 · BACK providers="+providers.size()+"\\npack="+packId+"\\n接著選配對 ROM。");
'''
    new_import='''        providers.clear();frontProviders.clear();JSONArray arr=m.getJSONArray("back_providers");
        for(int i=0;i<arr.length();i++){
            JSONObject o=arr.getJSONObject(i);Provider p=loadProvider(o);providers.put(p.species,p);
        }
        JSONArray front=m.optJSONArray("front_providers");if(front!=null)for(int i=0;i<front.length();i++){
            JSONObject o=front.getJSONObject(i);Provider p=loadProvider(o);frontProviders.put(p.species,p);
        }
        if(frontProviders.size()>1||(!frontProviders.isEmpty()&&!frontProviders.containsKey(155)))throw new Exception("R5 FRONT canary 僅允許火球鼠 #155");
        int[] ids=new int[providers.size()];int q=0;for(int id:providers.keySet())ids[q++]=id;nativeSetBackProviders(ids);
        int[] frontIds=new int[frontProviders.size()];q=0;for(int id:frontProviders.keySet())frontIds[q++]=id;nativeSetFrontProviders(frontIds);
        romButton.setEnabled(!providers.isEmpty());status.setVisibility(View.VISIBLE);status.setText("M6X1R5 SGXP 驗證成功 · BACK="+providers.size()+" · FRONT canary="+frontProviders.size()+"\\npack="+packId+"\\n接著選配對 ROM。");
'''
    text=replace_once(text,old_import,new_import,'R5 pack parser')

    query_anchor='    private String queryName(Uri uri){'
    helper='''    private Provider loadProvider(JSONObject o)throws Exception{
        Provider p=new Provider();p.species=o.getInt("species");p.name=o.optString("name","species_"+p.species);p.scale=(float)o.optDouble("scale",1.0);
        JSONArray fs=o.getJSONArray("frames");for(int k=0;k<fs.length();k++){JSONObject f=fs.getJSONObject(k);File img=new File(packDir,f.getString("path"));if(!img.isFile())throw new Exception("缺少 frame："+f.getString("path"));p.frames.add(new AnimFrame(img,Math.max(20,f.optInt("duration_ms",100))));}
        if(p.frames.isEmpty())throw new Exception("provider 無 frame："+p.name);return p;
    }
'''
    text=replace_once(text,query_anchor,helper+query_anchor,'provider parser helper')

    old_reg='int[] ids=new int[providers.size()];int q=0;for(int id:providers.keySet())ids[q++]=id;nativeSetBackProviders(ids);\n        gameView.startRuntime();'
    new_reg='int[] ids=new int[providers.size()];int q=0;for(int id:providers.keySet())ids[q++]=id;nativeSetBackProviders(ids);int[] frontIds=new int[frontProviders.size()];q=0;for(int id:frontProviders.keySet())frontIds[q++]=id;nativeSetFrontProviders(frontIds);\n        gameView.startRuntime();'
    text=replace_once(text,old_reg,new_reg,'front provider ROM re-registration')
    text=replace_once(text,
        'nativeBridgeAddress(),providers.size()));',
        'nativeBridgeAddress(),providers.size())+" · FRONT="+frontProviders.size());',
        'active status front count')

    text=replace_once(text,
        'j.put("external_pack_native_back_providers",providers.size());',
        'j.put("external_pack_native_back_providers",providers.size());j.put("external_pack_native_front_providers",frontProviders.size());j.put("front_canary_species",155);',
        'report front provider count')
    text=replace_once(text,
        'j.put("external_bridge_back_count_readback",nativeLastBackCountReadback());',
        'j.put("external_bridge_back_count_readback",nativeLastBackCountReadback());j.put("external_bridge_front_count_readback",nativeLastFrontCountReadback());',
        'report front bridge readback')
    text=replace_once(text,
        'j.put("external_overlay_frames",gameView.overlayFrames);j.put("external_overlay_failures",gameView.overlayFailures);j.put("external_active_species",gameView.activeSpecies);',
        'j.put("external_overlay_frames",gameView.overlayFrames);j.put("external_overlay_failures",gameView.overlayFailures);j.put("external_active_species",gameView.activeSpecies);'
        'j.put("external_front_overlay_frames",gameView.frontOverlayFrames);j.put("external_front_overlay_failures",gameView.frontOverlayFailures);j.put("external_front_active_species",gameView.activeFrontSpecies);'
        'j.put("front_proxy_generation_changes",gameView.frontProxyGenerationChanges);j.put("front_proxy_release_events",gameView.frontProxyReleaseEvents);j.put("front_proxy_hidden_edges",gameView.frontProxyHiddenEdges);j.put("front_proxy_monbg_visible_frames",gameView.frontProxyMonBgVisibleFrames);',
        'report front overlay telemetry')
    text=replace_once(text,
        'j.put("presentation_semantics","M6X1_R4_EDGE_TEARDOWN_GUARD");',
        'j.put("presentation_semantics","M6X1_R5_FRONT_CANARY");j.put("r4_runtime_authority","PASS_ACCEPTED_AYN_THOR");',
        'R5 presentation report')

    text=replace_once(text,
        'final int[]proxy=new int[14];final int[]presentation=new int[7];',
        'final int[]proxy=new int[14];final int[]enemyProxy=new int[14];final int[]presentation=new int[7];',
        'enemy proxy array')
    text=replace_once(text,
        'proxyGenerationChanges,proxyReleaseEvents,proxyHiddenEdges,proxyMonBgVisibleFrames;volatile int sourceQueuePeak,activeSpecies;',
        'proxyGenerationChanges,proxyReleaseEvents,proxyHiddenEdges,proxyMonBgVisibleFrames,frontOverlayFrames,frontOverlayFailures,frontProxyGenerationChanges,frontProxyReleaseEvents,frontProxyHiddenEdges,frontProxyMonBgVisibleFrames;volatile int sourceQueuePeak,activeSpecies,activeFrontSpecies;',
        'front counters')
    text=replace_once(text,
        'boolean presentationHadProxy,presentationVisibleOnce,lastPresentationVisible;int presentationSpecies,presentationSpriteId;long presentationEpochRomFrame;',
        'boolean presentationHadProxy,presentationVisibleOnce,lastPresentationVisible;int presentationSpecies,presentationSpriteId;long presentationEpochRomFrame;'
        'boolean frontPresentationHadProxy,frontPresentationVisibleOnce,frontLastPresentationVisible;int frontPresentationSpecies,frontPresentationSpriteId;long frontPresentationEpochRomFrame;',
        'front lifecycle state')
    text=replace_once(text,
        'bottomUiRestoreFrames=statOverlayFrames=statNativePatternFrames=statAssetFailures=statEdgeSafeFrames=proxyGenerationChanges=proxyReleaseEvents=proxyHiddenEdges=proxyMonBgVisibleFrames=0;sourceQueuePeak=activeSpecies=0;'
        'presentationHadProxy=presentationVisibleOnce=lastPresentationVisible=false;presentationSpecies=presentationSpriteId=0;presentationEpochRomFrame=0;',
        'bottomUiRestoreFrames=statOverlayFrames=statNativePatternFrames=statAssetFailures=statEdgeSafeFrames=proxyGenerationChanges=proxyReleaseEvents=proxyHiddenEdges=proxyMonBgVisibleFrames=frontOverlayFrames=frontOverlayFailures=frontProxyGenerationChanges=frontProxyReleaseEvents=frontProxyHiddenEdges=frontProxyMonBgVisibleFrames=0;sourceQueuePeak=activeSpecies=activeFrontSpecies=0;'
        'presentationHadProxy=presentationVisibleOnce=lastPresentationVisible=false;presentationSpecies=presentationSpriteId=0;presentationEpochRomFrame=0;'
        'frontPresentationHadProxy=frontPresentationVisibleOnce=frontLastPresentationVisible=false;frontPresentationSpecies=frontPresentationSpriteId=0;frontPresentationEpochRomFrame=0;',
        'front lifecycle reset')

    draw_marker='        @Override protected void onDraw(Canvas c){\n'
    enemy_helpers='''        private void resetFrontPresentationProxy(){
            frontPresentationHadProxy=frontPresentationVisibleOnce=frontLastPresentationVisible=false;
            frontPresentationSpecies=frontPresentationSpriteId=0;frontPresentationEpochRomFrame=0;
        }
        private boolean updateOpponentPresentationProxy(){
            if(nativeGetOpponentProxy(enemyProxy)!=1){if(frontPresentationHadProxy)frontProxyReleaseEvents++;resetFrontPresentationProxy();activeFrontSpecies=0;return false;}
            int species=enemyProxy[0],spriteId=enemyProxy[13];long romFrame=Integer.toUnsignedLong(enemyProxy[8]);boolean presentationVisible=enemyProxy[10]!=0;
            if(!frontPresentationHadProxy||species!=frontPresentationSpecies||spriteId!=frontPresentationSpriteId){
                if(frontPresentationHadProxy)frontProxyReleaseEvents++;frontPresentationHadProxy=true;frontPresentationSpecies=species;frontPresentationSpriteId=spriteId;
                frontPresentationVisibleOnce=false;frontLastPresentationVisible=false;frontPresentationEpochRomFrame=romFrame;frontProxyGenerationChanges++;
            }
            if(presentationVisible&&!frontPresentationVisibleOnce){frontPresentationVisibleOnce=true;frontPresentationEpochRomFrame=romFrame;}
            if(presentationVisible!=frontLastPresentationVisible){if(!presentationVisible&&frontLastPresentationVisible)frontProxyHiddenEdges++;frontLastPresentationVisible=presentationVisible;}
            if(enemyProxy[12]!=0&&presentationVisible)frontProxyMonBgVisibleFrames++;
            return presentationVisible&&frontPresentationVisibleOnce;
        }
        private void drawExternalOpponentFront(Canvas nc){
            if(!updateOpponentPresentationProxy())return;int species=enemyProxy[0];Provider p=frontProviders.get(species);
            if(p==null){frontOverlayFailures++;activeFrontSpecies=0;return;}long romFrame=Integer.toUnsignedLong(enemyProxy[8]);Bitmap frame=p.frameAtRomFrame(romFrame,frontPresentationEpochRomFrame,nativeFps());
            if(frame==null){frontOverlayFailures++;activeFrontSpecies=species;return;}float cx=enemyProxy[2]+enemyProxy[4],cy=enemyProxy[3]+enemyProxy[5],fw=frame.getWidth()*p.scale,fh=frame.getHeight()*p.scale;
            RectF dst=new RectF(cx-fw/2f,cy-fh/2f,cx+fw/2f,cy+fh/2f);nc.drawBitmap(frame,null,dst,paint);drawStatOverlayNative(nc,frame,dst,enemyProxy[1]);frontOverlayFrames++;activeFrontSpecies=species;
        }
'''
    text=replace_once(text,draw_marker,enemy_helpers+draw_marker,'front compositor helpers')
    text=replace_once(text,
        'Canvas nc=new Canvas(compositeBmp);nc.drawBitmap(bmp,0,0,paint);\n            if(updatePresentationProxy()){',
        'Canvas nc=new Canvas(compositeBmp);nc.drawBitmap(bmp,0,0,paint);drawExternalOpponentFront(nc);\n            if(updatePresentationProxy()){',
        'front-before-back draw order')

    required=[JAVA_MARKER,'nativeSetFrontProviders','nativeGetOpponentProxy','frontProviders','front_canary_species',
              'M6X1_R5_FRONT_CANARY','drawExternalOpponentFront(nc)','frontOverlayFrames','frontProxyGenerationChanges']
    missing=[x for x in required if x not in text]
    if missing: raise SystemExit('R5 Java verification missing: '+repr(missing))
    path.write_text(text)
    return 'patched'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--framework',required=True);ap.add_argument('--soulgold',required=True);a=ap.parse_args()
    fw=Path(a.framework);sg=Path(a.soulgold)
    cpp=patch_cpp(fw/'android/m6x1/app/src/main/cpp/native_bridge.cpp')
    java=patch_java(fw/'android/m6x1/app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java')
    # ROM R4 ownership/provider semantics are side-generic; R5 deliberately does not alter them.
    battle=(sg/'src/battle_main.c').read_text()
    if 'M6X1_R4_BATTLE_END_PROVIDER_LATCH' not in battle or 'M6X1_HostProvidesSpecies' not in battle:
        raise SystemExit('R4 side-generic ROM provider authority missing before R5')
    print('M6X1_R5_FRONT_CANARY_PATCH=PASS cpp='+cpp+' java='+java)
    print('front_canary_species='+str(CANARY_SPECIES))
    print('rom_changes=NONE_R4_SIDE_GENERIC_AUTHORITY_REUSED')

if __name__=='__main__':main()
