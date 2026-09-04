#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util

CPP_MARKER='M6X1_R1_PRESENTATION_BRIDGE_V2_ANDROID'


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
    text=text.replace(old,'static constexpr uint32_t kBridgeVersion=2u; // '+CPP_MARKER,1)
    old_struct='''  Proxy proxy[kBattlerCount];
};
static_assert(sizeof(Proxy)==44,"M6X1 Proxy ABI");
static_assert(sizeof(Bridge)==332,"M6X1 Bridge ABI");'''
    new_struct='''  Proxy proxy[kBattlerCount];
  uint32_t statActive,statBattler,statDecrease,statPal,statSharp,statBlend;
  int32_t statScroll;
};
static_assert(sizeof(Proxy)==44,"M6X1 Proxy ABI");
static_assert(sizeof(Bridge)==360,"M6X1 Bridge ABI v2");'''
    if old_struct not in text:raise SystemExit('native Bridge ABI anchor missing')
    text=text.replace(old_struct,new_struct,1)
    anchor='''extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPlayerProxy(JNIEnv*e,jclass,jintArray out){
  if(!gBridgeFresh.load(std::memory_order_relaxed)||!out||e->GetArrayLength(out)<10)return 0;Bridge b{};{std::lock_guard<std::mutex>lk(gBridgeMu);b=gCachedBridge;}
  for(const Proxy&p:b.proxy){if(p.valid&&p.side==0&&p.visible&&isBackProvider(p.species)){jint v[10]={(jint)p.species,(jint)p.battler,(jint)p.x,(jint)p.y,(jint)p.x2,(jint)p.y2,(jint)p.hFlip,(jint)p.vFlip,(jint)b.romFrame,(jint)p.side};e->SetIntArrayRegion(out,0,10,v);return 1;}}
  return 0;
}
'''
    if anchor not in text:raise SystemExit('nativeGetPlayerProxy anchor missing')
    addition=r'''
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPresentationState(JNIEnv*e,jclass,jintArray out){
  if(!gBridgeFresh.load(std::memory_order_relaxed)||!out||e->GetArrayLength(out)<7)return 0;
  Bridge b{};{std::lock_guard<std::mutex>lk(gBridgeMu);b=gCachedBridge;}
  jint v[7]={(jint)b.statActive,(jint)b.statBattler,(jint)b.statDecrease,(jint)b.statPal,(jint)b.statSharp,(jint)b.statBlend,(jint)b.statScroll};
  e->SetIntArrayRegion(out,0,7,v);return 1;
}
'''
    text=text.replace(anchor,anchor+addition,1)
    path.write_text(text);return 'patched'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args();root=Path(a.root)
    cpp=patch_cpp(root/'app/src/main/cpp/native_bridge.cpp')
    mod=load_java_patcher();java=mod.patch_java(root/'app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java')
    print('M6X1_ANDROID_PRESENTATION_V2=PASS cpp='+cpp+' java='+java)

if __name__=='__main__':main()
