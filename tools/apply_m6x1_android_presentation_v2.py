#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util

CPP_MARKER='M6X1_R2_PRESENTATION_BRIDGE_V3_ANDROID'


def load_java_patcher():
    p=Path(__file__).with_name('apply_m6x1_android_presentation_patch.py')
    spec=importlib.util.spec_from_file_location('m6x1_java_presentation',p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def patch_cpp(path:Path):
    text=path.read_text()
    if CPP_MARKER in text:return 'already'

    old='static constexpr uint32_t kBridgeVersion=1u;'
    if old not in text:raise SystemExit('native bridge version anchor missing')
    text=text.replace(old,'static constexpr uint32_t kBridgeVersion=3u; // '+CPP_MARKER,1)

    old_proxy='''struct Proxy {
  uint32_t valid,species,side,battler,visible;
  int32_t x,y,x2,y2;
  uint32_t hFlip,vFlip;
};'''
    new_proxy='''struct Proxy {
  uint32_t valid,species,side,battler,visible;
  uint32_t nativeVisible,monBgActive,spriteId;
  int32_t x,y,x2,y2;
  uint32_t hFlip,vFlip;
};'''
    if old_proxy not in text:raise SystemExit('native Proxy ABI anchor missing')
    text=text.replace(old_proxy,new_proxy,1)

    old_struct='''  Proxy proxy[kBattlerCount];
};
static_assert(sizeof(Proxy)==44,"M6X1 Proxy ABI");
static_assert(sizeof(Bridge)==332,"M6X1 Bridge ABI");'''
    new_struct='''  Proxy proxy[kBattlerCount];
  uint32_t statActive,statBattler,statDecrease,statPal,statSharp,statBlend;
  int32_t statScroll;
};
static_assert(sizeof(Proxy)==56,"M6X1 Proxy ABI v3");
static_assert(sizeof(Bridge)==408,"M6X1 Bridge ABI v3");'''
    if old_struct not in text:raise SystemExit('native Bridge ABI anchor missing')
    text=text.replace(old_struct,new_struct,1)

    fresh='static std::atomic<bool> gBridgeFresh{false};\n'
    if fresh not in text:raise SystemExit('gBridgeFresh anchor missing')
    text=text.replace(fresh,fresh+'static std::atomic<bool> gCachedBridgeValid{false}; // M6X1_R2_LAST_KNOWN_GOOD_SNAPSHOT\n',1)

    # R1 invalidated the shared snapshot at the beginning of every core frame.
    # The Choreographer thread could sample that tiny false window and omit the
    # Showdown body for one display frame. R2 keeps last-known-good readable and
    # atomically replaces it only after the new bridge passes validation.
    race='gRegistryAttempts.fetch_add(1,std::memory_order_relaxed);gBridgeFresh=false;'
    if race not in text:raise SystemExit('syncBridge transient invalidation anchor missing')
    text=text.replace(race,'gRegistryAttempts.fetch_add(1,std::memory_order_relaxed);',1)
    text=text.replace('if(M6X1_BRIDGE_EWRAM_ADDRESS<kEwramBase){gLastBridgeError=1;gRegistryFailures++;return;}',
                      'if(M6X1_BRIDGE_EWRAM_ADDRESS<kEwramBase){gBridgeFresh=false;gLastBridgeError=1;gRegistryFailures++;return;}',1)
    text=text.replace('if(!ram||off+sizeof(Bridge)>n){gLastBridgeError=2;gRegistryFailures++;return;}',
                      'if(!ram||off+sizeof(Bridge)>n){gBridgeFresh=false;gLastBridgeError=2;gRegistryFailures++;return;}',1)
    text=text.replace('if(b->hostMagic!=kHostMagic||b->backCount!=(uint32_t)std::min<size_t>(gBackProviders.size(),kProviderCapacity)){gLastBridgeError=3;gRegistryFailures++;return;}',
                      'if(b->hostMagic!=kHostMagic||b->backCount!=(uint32_t)std::min<size_t>(gBackProviders.size(),kProviderCapacity)){gBridgeFresh=false;gLastBridgeError=3;gRegistryFailures++;return;}',1)

    commit='''    std::lock_guard<std::mutex> lk(gBridgeMu);std::memcpy(&gCachedBridge,b,sizeof(Bridge));gLastRomFrame=b->romFrame;gBridgeFresh=true;'''
    commit2='''    std::lock_guard<std::mutex> lk(gBridgeMu);std::memcpy(&gCachedBridge,b,sizeof(Bridge));gLastRomFrame=b->romFrame;gCachedBridgeValid=true;gBridgeFresh=true;'''
    if commit not in text:raise SystemExit('bridge snapshot commit anchor missing')
    text=text.replace(commit,commit2,1)

    reset='gHostEpoch=0;gLastRomFrame=0;gBridgeFresh=false;gLastBridgeError=0;'
    if reset not in text:raise SystemExit('bridge load reset anchor missing')
    text=text.replace(reset,'gHostEpoch=0;gLastRomFrame=0;gBridgeFresh=false;gCachedBridgeValid=false;gLastBridgeError=0;',1)

    old_get='''extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPlayerProxy(JNIEnv*e,jclass,jintArray out){
  if(!gBridgeFresh.load(std::memory_order_relaxed)||!out||e->GetArrayLength(out)<10)return 0;Bridge b{};{std::lock_guard<std::mutex>lk(gBridgeMu);b=gCachedBridge;}
  for(const Proxy&p:b.proxy){if(p.valid&&p.side==0&&p.visible&&isBackProvider(p.species)){jint v[10]={(jint)p.species,(jint)p.battler,(jint)p.x,(jint)p.y,(jint)p.x2,(jint)p.y2,(jint)p.hFlip,(jint)p.vFlip,(jint)b.romFrame,(jint)p.side};e->SetIntArrayRegion(out,0,10,v);return 1;}}
  return 0;
}
'''
    new_get='''extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPlayerProxy(JNIEnv*e,jclass,jintArray out){
  if(!gCachedBridgeValid.load(std::memory_order_acquire)||!out||e->GetArrayLength(out)<14)return 0;
  Bridge b{};{std::lock_guard<std::mutex>lk(gBridgeMu);b=gCachedBridge;}
  for(const Proxy&p:b.proxy){
    if(p.valid&&p.side==0&&isBackProvider(p.species)){
      jint v[14]={(jint)p.species,(jint)p.battler,(jint)p.x,(jint)p.y,(jint)p.x2,(jint)p.y2,
                  (jint)p.hFlip,(jint)p.vFlip,(jint)b.romFrame,(jint)p.side,(jint)p.visible,
                  (jint)p.nativeVisible,(jint)p.monBgActive,(jint)p.spriteId};
      e->SetIntArrayRegion(out,0,14,v);return 1;
    }
  }
  return 0;
}
'''
    if old_get not in text:raise SystemExit('nativeGetPlayerProxy v1 anchor missing')
    text=text.replace(old_get,new_get,1)

    addition='''extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPresentationState(JNIEnv*e,jclass,jintArray out){
  if(!gCachedBridgeValid.load(std::memory_order_acquire)||!out||e->GetArrayLength(out)<7)return 0;
  Bridge b{};{std::lock_guard<std::mutex>lk(gBridgeMu);b=gCachedBridge;}
  jint v[7]={(jint)b.statActive,(jint)b.statBattler,(jint)b.statDecrease,(jint)b.statPal,(jint)b.statSharp,(jint)b.statBlend,(jint)b.statScroll};
  e->SetIntArrayRegion(out,0,7,v);return 1;
}
'''
    text=text.replace(new_get,new_get+addition,1)
    path.write_text(text);return 'patched'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args();root=Path(a.root)
    cpp=patch_cpp(root/'app/src/main/cpp/native_bridge.cpp')
    mod=load_java_patcher();java=mod.patch_java(root/'app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java')
    print('M6X1_ANDROID_PRESENTATION_R2=PASS cpp='+cpp+' java='+java)

if __name__=='__main__':main()
