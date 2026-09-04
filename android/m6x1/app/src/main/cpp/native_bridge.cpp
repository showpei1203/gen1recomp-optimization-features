#include <jni.h>
#include <android/log.h>
#include <dlfcn.h>
#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <deque>
#include <fstream>
#include <mutex>
#include <string>
#include <vector>
#include "generated_bridge.h"

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"SoulGoldM6X1",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"SoulGoldM6X1",__VA_ARGS__)

using retro_environment_t = bool (*)(unsigned, void*);
using retro_video_refresh_t = void (*)(const void*, unsigned, unsigned, size_t);
using retro_audio_sample_t = void (*)(int16_t,int16_t);
using retro_audio_sample_batch_t = size_t (*)(const int16_t*, size_t);
using retro_input_poll_t = void (*)(void);
using retro_input_state_t = int16_t (*)(unsigned,unsigned,unsigned,unsigned);

struct retro_game_info { const char* path; const void* data; size_t size; const char* meta; };
struct retro_game_geometry { unsigned base_width, base_height, max_width, max_height; float aspect_ratio; };
struct retro_system_timing { double fps, sample_rate; };
struct retro_system_av_info { retro_game_geometry geometry; retro_system_timing timing; };

enum { RETRO_PIXEL_FORMAT_0RGB1555=0, RETRO_PIXEL_FORMAT_XRGB8888=1, RETRO_PIXEL_FORMAT_RGB565=2 };
enum { RETRO_DEVICE_JOYPAD=1, RETRO_DEVICE_ID_JOYPAD_MASK=256 };
enum { RETRO_MEMORY_SAVE_RAM=0, RETRO_MEMORY_RTC=1, RETRO_MEMORY_SYSTEM_RAM=2, RETRO_MEMORY_VIDEO_RAM=3 };
enum {
  ENV_GET_CAN_DUPE=3, ENV_GET_SYSTEM_DIRECTORY=9, ENV_SET_PIXEL_FORMAT=10,
  ENV_SET_INPUT_DESCRIPTORS=11, ENV_GET_VARIABLE=15, ENV_SET_VARIABLES=16,
  ENV_GET_VARIABLE_UPDATE=17, ENV_SET_SUPPORT_NO_GAME=18,
  ENV_GET_SAVE_DIRECTORY=31, ENV_SET_SYSTEM_AV_INFO=32, ENV_SET_MEMORY_MAPS=36,
  ENV_SET_GEOMETRY=37, ENV_SET_SUPPORT_ACHIEVEMENTS=42
};

static constexpr uint32_t kRomMagic=0x4D365831u;
static constexpr uint32_t kHostMagic=0x53475831u;
static constexpr uint32_t kBridgeVersion=1u;
static constexpr uint32_t kEwramBase=0x02000000u;
static constexpr size_t kProviderCapacity=16;
static constexpr size_t kBattlerCount=4;

struct Proxy {
  uint32_t valid,species,side,battler,visible;
  int32_t x,y,x2,y2;
  uint32_t hFlip,vFlip;
};
struct Bridge {
  uint32_t romMagic,version,romFrame;
  uint32_t hostMagic,hostEpoch,backCount,frontCount;
  uint32_t backSpecies[kProviderCapacity];
  uint32_t frontSpecies[kProviderCapacity];
  Proxy proxy[kBattlerCount];
};
static_assert(sizeof(Proxy)==44,"M6X1 Proxy ABI");
static_assert(sizeof(Bridge)==332,"M6X1 Bridge ABI");

struct Core {
  void* so=nullptr;
  void (*set_environment)(retro_environment_t)=nullptr;
  void (*set_video_refresh)(retro_video_refresh_t)=nullptr;
  void (*set_audio_sample)(retro_audio_sample_t)=nullptr;
  void (*set_audio_sample_batch)(retro_audio_sample_batch_t)=nullptr;
  void (*set_input_poll)(retro_input_poll_t)=nullptr;
  void (*set_input_state)(retro_input_state_t)=nullptr;
  void (*init)()=nullptr;
  void (*deinit)()=nullptr;
  bool (*load_game)(const retro_game_info*)=nullptr;
  void (*unload_game)()=nullptr;
  void (*run)()=nullptr;
  void (*reset)()=nullptr;
  void (*get_system_av_info)(retro_system_av_info*)=nullptr;
  void* (*get_memory_data)(unsigned)=nullptr;
  size_t (*get_memory_size)(unsigned)=nullptr;
};

static Core g;
static bool gInitialized=false;
static std::atomic<bool> gLoaded{false};
static std::string gSystemDir,gSaveDir,gLastError;
static std::vector<uint8_t> gRom;
static std::vector<uint32_t> gFrame;
static unsigned gW=240,gH=160;
static int gPixelFmt=RETRO_PIXEL_FORMAT_RGB565;
static std::mutex gFrameMu,gAudioMu,gBridgeMu;
static std::deque<int16_t> gAudio;
static std::atomic<uint32_t> gInput{0};
static double gFps=59.7275009155;
static double gReportedRate=32768.0;
static double gEffectiveRate=65536.0;
static std::atomic<uint64_t> gAudioGeneratedSamples{0},gAudioDrainedSamples{0},gAudioDroppedSamples{0};
static std::atomic<uint64_t> gCoreFrames{0};
static std::vector<uint32_t> gBackProviders;
static Bridge gCachedBridge{};
static std::atomic<bool> gBridgeFresh{false};
static uint32_t gLastRomFrame=0;
static std::atomic<uint64_t> gRegistryAttempts{0},gRegistrySyncs{0},gRegistryFailures{0};
static std::atomic<uint32_t> gHostEpoch{0};
static std::atomic<uint32_t> gLastRomMagic{0},gLastBridgeVersion{0},gLastHostReadback{0},gLastBackCountReadback{0};
static std::atomic<uint32_t> gLastBridgeError{0};

static bool envCb(unsigned cmd,void* data){
  switch(cmd){
    case ENV_GET_CAN_DUPE: if(data)*(bool*)data=true; return true;
    case ENV_GET_SYSTEM_DIRECTORY: if(data)*(const char**)data=gSystemDir.c_str(); return true;
    case ENV_GET_SAVE_DIRECTORY: if(data)*(const char**)data=gSaveDir.c_str(); return true;
    case ENV_SET_PIXEL_FORMAT: if(data)gPixelFmt=*(int*)data; return true;
    case ENV_SET_INPUT_DESCRIPTORS: case ENV_SET_VARIABLES: case ENV_SET_MEMORY_MAPS:
    case ENV_SET_SUPPORT_ACHIEVEMENTS: case ENV_SET_GEOMETRY: case ENV_SET_SYSTEM_AV_INFO: return true;
    case ENV_GET_VARIABLE: return false;
    case ENV_GET_VARIABLE_UPDATE: if(data)*(bool*)data=false; return true;
    case ENV_SET_SUPPORT_NO_GAME: return true;
    default: return false;
  }
}
static inline uint32_t rgb565(uint16_t p){
  uint32_t r=(p>>11)&31,gg=(p>>5)&63,b=p&31; r=(r<<3)|(r>>2);gg=(gg<<2)|(gg>>4);b=(b<<3)|(b>>2);
  return 0xFF000000u|(r<<16)|(gg<<8)|b;
}
static inline uint32_t rgb1555(uint16_t p){
  uint32_t r=(p>>10)&31,gg=(p>>5)&31,b=p&31;r=(r<<3)|(r>>2);gg=(gg<<3)|(gg>>2);b=(b<<3)|(b>>2);
  return 0xFF000000u|(r<<16)|(gg<<8)|b;
}
static void videoCb(const void* data,unsigned w,unsigned h,size_t pitch){
  if(!data||data==(const void*)(intptr_t)-1||!w||!h)return;
  std::lock_guard<std::mutex> lk(gFrameMu);gW=w;gH=h;gFrame.resize((size_t)w*h);
  if(gPixelFmt==RETRO_PIXEL_FORMAT_XRGB8888){
    for(unsigned y=0;y<h;y++){auto*s=(const uint32_t*)((const uint8_t*)data+y*pitch);for(unsigned x=0;x<w;x++)gFrame[(size_t)y*w+x]=0xFF000000u|(s[x]&0x00FFFFFFu);}
  }else{
    for(unsigned y=0;y<h;y++){auto*s=(const uint16_t*)((const uint8_t*)data+y*pitch);for(unsigned x=0;x<w;x++)gFrame[(size_t)y*w+x]=(gPixelFmt==RETRO_PIXEL_FORMAT_RGB565)?rgb565(s[x]):rgb1555(s[x]);}
  }
}
static void audioOne(int16_t l,int16_t r){
  std::lock_guard<std::mutex> lk(gAudioMu);gAudio.push_back(l);gAudio.push_back(r);gAudioGeneratedSamples.fetch_add(2,std::memory_order_relaxed);
}
static size_t audioBatch(const int16_t* p,size_t frames){
  if(!p||!frames)return frames;
  std::lock_guard<std::mutex> lk(gAudioMu);
  const size_t samples=frames*2;
  for(size_t i=0;i<samples;i++)gAudio.push_back(p[i]);
  gAudioGeneratedSamples.fetch_add(samples,std::memory_order_relaxed);
  // M6X1 deliberately does not delete live PCM to repair latency. Keep a large
  // emergency ceiling only to prevent OOM if the Java sink is destroyed.
  const size_t emergencyMax=65536u*2u*4u;
  while(gAudio.size()>emergencyMax){gAudio.pop_front();gAudioDroppedSamples.fetch_add(1,std::memory_order_relaxed);}
  return frames;
}
static void inputPoll(){}
static int16_t inputState(unsigned port,unsigned device,unsigned index,unsigned id){
  (void)index;if(port!=0||device!=RETRO_DEVICE_JOYPAD)return 0;uint32_t m=gInput.load(std::memory_order_relaxed);
  if(id==RETRO_DEVICE_ID_JOYPAD_MASK)return(int16_t)m;return id<16?((m>>id)&1u):0;
}

template<typename T>static bool sym(T&out,const char*n){out=reinterpret_cast<T>(dlsym(g.so,n));if(!out){gLastError=std::string("missing symbol: ")+n;return false;}return true;}
static void closeCore(){
  if(gLoaded.exchange(false)&&g.unload_game)g.unload_game();if(gInitialized&&g.deinit)g.deinit();gInitialized=false;if(g.so)dlclose(g.so);g=Core{};gRom.clear();
}
static bool openCore(const std::string&libDir){
  closeCore();std::string p=libDir+"/libmgba_libretro.so";g.so=dlopen(p.c_str(),RTLD_NOW|RTLD_LOCAL);
  if(!g.so){const char*e=dlerror();gLastError=e?e:"dlopen failed";return false;}
  if(!sym(g.set_environment,"retro_set_environment")||!sym(g.set_video_refresh,"retro_set_video_refresh")||!sym(g.set_audio_sample,"retro_set_audio_sample")||!sym(g.set_audio_sample_batch,"retro_set_audio_sample_batch")||!sym(g.set_input_poll,"retro_set_input_poll")||!sym(g.set_input_state,"retro_set_input_state")||!sym(g.init,"retro_init")||!sym(g.deinit,"retro_deinit")||!sym(g.load_game,"retro_load_game")||!sym(g.unload_game,"retro_unload_game")||!sym(g.run,"retro_run")||!sym(g.reset,"retro_reset")||!sym(g.get_system_av_info,"retro_get_system_av_info")||!sym(g.get_memory_data,"retro_get_memory_data")||!sym(g.get_memory_size,"retro_get_memory_size")){closeCore();return false;}
  g.set_environment(envCb);g.set_video_refresh(videoCb);g.set_audio_sample(audioOne);g.set_audio_sample_batch(audioBatch);g.set_input_poll(inputPoll);g.set_input_state(inputState);g.init();gInitialized=true;return true;
}
static bool readFile(const std::string&p,std::vector<uint8_t>&out){std::ifstream f(p,std::ios::binary|std::ios::ate);if(!f)return false;auto n=f.tellg();if(n<=0||n>128*1024*1024)return false;out.resize((size_t)n);f.seekg(0);f.read((char*)out.data(),n);return!!f;}
static bool saveSram(const std::string&path){if(!gLoaded||!g.get_memory_size||!g.get_memory_data)return false;size_t n=g.get_memory_size(RETRO_MEMORY_SAVE_RAM);void*p=g.get_memory_data(RETRO_MEMORY_SAVE_RAM);if(!n||!p)return false;std::ofstream f(path,std::ios::binary|std::ios::trunc);if(!f)return false;f.write((char*)p,n);return!!f;}
static bool loadSram(const std::string&path){if(!gLoaded||!g.get_memory_size||!g.get_memory_data)return false;size_t n=g.get_memory_size(RETRO_MEMORY_SAVE_RAM);void*p=g.get_memory_data(RETRO_MEMORY_SAVE_RAM);if(!n||!p)return false;std::ifstream f(path,std::ios::binary);if(!f)return false;f.read((char*)p,n);return f.gcount()>0;}

static bool isBackProvider(uint32_t species){for(uint32_t s:gBackProviders)if(s==species)return true;return false;}
static void syncBridge(){
  gRegistryAttempts.fetch_add(1,std::memory_order_relaxed);gBridgeFresh=false;
  if(M6X1_BRIDGE_EWRAM_ADDRESS<kEwramBase){gLastBridgeError=1;gRegistryFailures++;return;}
  void*ram=g.get_memory_data?g.get_memory_data(RETRO_MEMORY_SYSTEM_RAM):nullptr;
  size_t n=g.get_memory_size?g.get_memory_size(RETRO_MEMORY_SYSTEM_RAM):0;
  const size_t off=(size_t)(M6X1_BRIDGE_EWRAM_ADDRESS-kEwramBase);
  if(!ram||off+sizeof(Bridge)>n){gLastBridgeError=2;gRegistryFailures++;return;}
  auto*b=(Bridge*)((uint8_t*)ram+off);
  const uint32_t epoch=gHostEpoch.fetch_add(1,std::memory_order_relaxed)+1;
  b->hostMagic=kHostMagic;b->hostEpoch=epoch;
  b->backCount=(uint32_t)std::min<size_t>(gBackProviders.size(),kProviderCapacity);b->frontCount=0;
  std::memset(b->backSpecies,0,sizeof(b->backSpecies));std::memset(b->frontSpecies,0,sizeof(b->frontSpecies));
  for(size_t i=0;i<b->backCount;i++)b->backSpecies[i]=gBackProviders[i];
  std::atomic_thread_fence(std::memory_order_seq_cst);
  gLastHostReadback=b->hostMagic;gLastBackCountReadback=b->backCount;gLastRomMagic=b->romMagic;gLastBridgeVersion=b->version;
  if(b->hostMagic!=kHostMagic||b->backCount!=(uint32_t)std::min<size_t>(gBackProviders.size(),kProviderCapacity)){gLastBridgeError=3;gRegistryFailures++;return;}
  gRegistrySyncs.fetch_add(1,std::memory_order_relaxed);gLastBridgeError=0;
  if(b->romMagic==kRomMagic&&b->version==kBridgeVersion&&b->romFrame!=gLastRomFrame){
    std::lock_guard<std::mutex> lk(gBridgeMu);std::memcpy(&gCachedBridge,b,sizeof(Bridge));gLastRomFrame=b->romFrame;gBridgeFresh=true;
  }
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeInit(JNIEnv*e,jclass,jstring lib,jstring files){const char*a=e->GetStringUTFChars(lib,nullptr);const char*b=e->GetStringUTFChars(files,nullptr);std::string ld=a,fd=b;e->ReleaseStringUTFChars(lib,a);e->ReleaseStringUTFChars(files,b);gSystemDir=fd;gSaveDir=fd;gLastError.clear();return openCore(ld)?JNI_TRUE:JNI_FALSE;}
extern "C" JNIEXPORT jboolean JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLoadRom(JNIEnv*e,jclass,jstring rom,jstring save){
  const char*rp=e->GetStringUTFChars(rom,nullptr);const char*sp=e->GetStringUTFChars(save,nullptr);std::string r=rp,s=sp;e->ReleaseStringUTFChars(rom,rp);e->ReleaseStringUTFChars(save,sp);
  if(gLoaded.exchange(false)&&g.unload_game)g.unload_game();if(!readFile(r,gRom)){gLastError="ROM read failed";return JNI_FALSE;}retro_game_info info{r.c_str(),gRom.data(),gRom.size(),nullptr};if(!g.load_game(&info)){gLastError="mGBA retro_load_game failed";return JNI_FALSE;}
  gLoaded=true;retro_system_av_info av{};g.get_system_av_info(&av);gFps=av.timing.fps;gReportedRate=av.timing.sample_rate;
  // Pinned mGBA/SoulGold authority: this runtime emits ~65536 stereo frames/s even
  // though AV info reports 32768. M6X0 THOR telemetry and sealed M1.4 both prove it.
  gEffectiveRate=(gReportedRate>=30000.0&&gReportedRate<=34000.0)?gReportedRate*2.0:gReportedRate;
  gAudioGeneratedSamples=0;gAudioDrainedSamples=0;gAudioDroppedSamples=0;gCoreFrames=0;gRegistryAttempts=0;gRegistrySyncs=0;gRegistryFailures=0;gHostEpoch=0;gLastRomFrame=0;gBridgeFresh=false;gLastBridgeError=0;
  {std::lock_guard<std::mutex>lk(gAudioMu);gAudio.clear();}{std::lock_guard<std::mutex>lk(gBridgeMu);std::memset(&gCachedBridge,0,sizeof(gCachedBridge));}
  loadSram(s);LOGI("ROM loaded bytes=%zu fps=%.6f reported_audio=%.1f effective_audio=%.1f bridge=0x%08x",gRom.size(),gFps,gReportedRate,gEffectiveRate,M6X1_BRIDGE_EWRAM_ADDRESS);return JNI_TRUE;
}
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeSetBackProviders(JNIEnv*e,jclass,jintArray arr){std::vector<jint>v;if(arr){jsize n=e->GetArrayLength(arr);n=std::min<jsize>(n,(jsize)kProviderCapacity);v.resize(n);e->GetIntArrayRegion(arr,0,n,v.data());}gBackProviders.clear();for(jint x:v)if(x>0)gBackProviders.push_back((uint32_t)x);}
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeRunFrame(JNIEnv*,jclass){if(gLoaded&&g.run){g.run();gCoreFrames++;syncBridge();}}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeCopyFrame(JNIEnv*e,jclass,jintArray arr){std::lock_guard<std::mutex>lk(gFrameMu);jsize n=e->GetArrayLength(arr);size_t need=gFrame.size();if((size_t)n<need)return-(jint)need;if(need)e->SetIntArrayRegion(arr,0,(jsize)need,(const jint*)gFrame.data());return(jint)((gW<<16)|(gH&0xFFFF));}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPlayerProxy(JNIEnv*e,jclass,jintArray out){
  if(!gBridgeFresh.load(std::memory_order_relaxed)||!out||e->GetArrayLength(out)<10)return 0;Bridge b{};{std::lock_guard<std::mutex>lk(gBridgeMu);b=gCachedBridge;}
  for(const Proxy&p:b.proxy){if(p.valid&&p.side==0&&p.visible&&isBackProvider(p.species)){jint v[10]={(jint)p.species,(jint)p.battler,(jint)p.x,(jint)p.y,(jint)p.x2,(jint)p.y2,(jint)p.hFlip,(jint)p.vFlip,(jint)b.romFrame,(jint)p.side};e->SetIntArrayRegion(out,0,10,v);return 1;}}
  return 0;
}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeDrainAudio(JNIEnv*e,jclass,jshortArray arr){std::lock_guard<std::mutex>lk(gAudioMu);jsize cap=e->GetArrayLength(arr);int n=(int)std::min<size_t>((size_t)cap,gAudio.size());if(!n)return 0;std::vector<jshort>tmp(n);for(int i=0;i<n;i++){tmp[i]=gAudio.front();gAudio.pop_front();}e->SetShortArrayRegion(arr,0,n,tmp.data());gAudioDrainedSamples.fetch_add((uint64_t)n,std::memory_order_relaxed);return n;}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeAudioQueueSamples(JNIEnv*,jclass){std::lock_guard<std::mutex>lk(gAudioMu);return(jint)gAudio.size();}
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeAudioGeneratedSamples(JNIEnv*,jclass){return(jlong)gAudioGeneratedSamples.load();}
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeAudioDrainedSamples(JNIEnv*,jclass){return(jlong)gAudioDrainedSamples.load();}
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeAudioDroppedSamples(JNIEnv*,jclass){return(jlong)gAudioDroppedSamples.load();}
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeSetInputMask(JNIEnv*,jclass,jint m){gInput=(uint32_t)m;}
extern "C" JNIEXPORT jdouble JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeFps(JNIEnv*,jclass){return gFps;}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeReportedSampleRate(JNIEnv*,jclass){return(jint)(gReportedRate+0.5);}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeEffectiveSampleRate(JNIEnv*,jclass){return(jint)(gEffectiveRate+0.5);}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeBridgeAddress(JNIEnv*,jclass){return(jint)M6X1_BRIDGE_EWRAM_ADDRESS;}
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeRegistryAttempts(JNIEnv*,jclass){return(jlong)gRegistryAttempts.load();}
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeRegistrySyncs(JNIEnv*,jclass){return(jlong)gRegistrySyncs.load();}
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeRegistryFailures(JNIEnv*,jclass){return(jlong)gRegistryFailures.load();}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLastRomMagic(JNIEnv*,jclass){return(jint)gLastRomMagic.load();}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLastBridgeVersion(JNIEnv*,jclass){return(jint)gLastBridgeVersion.load();}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLastHostReadback(JNIEnv*,jclass){return(jint)gLastHostReadback.load();}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLastBackCountReadback(JNIEnv*,jclass){return(jint)gLastBackCountReadback.load();}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLastBridgeError(JNIEnv*,jclass){return(jint)gLastBridgeError.load();}
extern "C" JNIEXPORT jboolean JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeBridgeFresh(JNIEnv*,jclass){return gBridgeFresh.load()?JNI_TRUE:JNI_FALSE;}
extern "C" JNIEXPORT jboolean JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeSaveSram(JNIEnv*e,jclass,jstring save){const char*s=e->GetStringUTFChars(save,nullptr);bool ok=saveSram(s);e->ReleaseStringUTFChars(save,s);return ok?JNI_TRUE:JNI_FALSE;}
extern "C" JNIEXPORT jstring JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeLastError(JNIEnv*e,jclass){return e->NewStringUTF(gLastError.c_str());}
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeReset(JNIEnv*,jclass){if(gLoaded&&g.reset)g.reset();}
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeShutdown(JNIEnv*,jclass){closeCore();}
