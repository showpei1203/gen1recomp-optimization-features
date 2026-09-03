#include <jni.h>
#include <android/log.h>
#include <dlfcn.h>
#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <mutex>
#include <string>
#include <vector>
#include <deque>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"SoulGoldM6A2",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"SoulGoldM6A2",__VA_ARGS__)

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
enum {
  ENV_GET_CAN_DUPE=3, ENV_GET_SYSTEM_DIRECTORY=9, ENV_SET_PIXEL_FORMAT=10,
  ENV_SET_INPUT_DESCRIPTORS=11, ENV_GET_VARIABLE=15, ENV_SET_VARIABLES=16,
  ENV_GET_VARIABLE_UPDATE=17, ENV_SET_SUPPORT_NO_GAME=18, ENV_GET_RUMBLE_INTERFACE=23,
  ENV_GET_SENSOR_INTERFACE=25, ENV_GET_CAMERA_INTERFACE=26, ENV_GET_LOG_INTERFACE=27,
  ENV_GET_SAVE_DIRECTORY=31, ENV_SET_SYSTEM_AV_INFO=32, ENV_SET_MEMORY_MAPS=36,
  ENV_SET_GEOMETRY=37, ENV_SET_SUPPORT_ACHIEVEMENTS=42
};

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
static bool g_initialized=false;
static std::string g_systemDir, g_saveDir, g_lastError;
static std::vector<uint8_t> g_rom;
static std::vector<uint32_t> g_frame;
static unsigned g_w=240,g_h=160;
static int g_pixelFmt=RETRO_PIXEL_FORMAT_RGB565;
static std::mutex g_frameMu, g_audioMu;
static std::deque<int16_t> g_audio;
static std::atomic<uint32_t> g_input{0};
static std::atomic<bool> g_loaded{false};
static double g_fps=59.7275, g_sampleRate=32768.0;
static std::atomic<uint64_t> g_audioGeneratedSamples{0};
static std::atomic<uint64_t> g_audioDrainedSamples{0};
static std::atomic<uint64_t> g_audioDroppedSamples{0};

static bool env_cb(unsigned cmd, void* data) {
  switch (cmd) {
    case ENV_GET_CAN_DUPE: if(data) *(bool*)data=true; return true;
    case ENV_GET_SYSTEM_DIRECTORY: if(data) *(const char**)data=g_systemDir.c_str(); return true;
    case ENV_GET_SAVE_DIRECTORY: if(data) *(const char**)data=g_saveDir.c_str(); return true;
    case ENV_SET_PIXEL_FORMAT: if(data) g_pixelFmt=*(int*)data; return true;
    case ENV_SET_INPUT_DESCRIPTORS: case ENV_SET_VARIABLES: case ENV_SET_MEMORY_MAPS:
    case ENV_SET_SUPPORT_ACHIEVEMENTS: case ENV_SET_GEOMETRY: case ENV_SET_SYSTEM_AV_INFO:
      return true;
    case ENV_GET_VARIABLE: return false;
    case ENV_GET_VARIABLE_UPDATE: if(data) *(bool*)data=false; return true;
    case ENV_SET_SUPPORT_NO_GAME: return true;
    default: return false;
  }
}

static inline uint32_t rgb565(uint16_t p) {
  uint32_t r=(p>>11)&31, gg=(p>>5)&63, b=p&31;
  r=(r<<3)|(r>>2); gg=(gg<<2)|(gg>>4); b=(b<<3)|(b>>2);
  return 0xFF000000u | (r<<16) | (gg<<8) | b;
}
static inline uint32_t rgb1555(uint16_t p) {
  uint32_t r=(p>>10)&31, gg=(p>>5)&31, b=p&31;
  r=(r<<3)|(r>>2); gg=(gg<<3)|(gg>>2); b=(b<<3)|(b>>2);
  return 0xFF000000u | (r<<16) | (gg<<8) | b;
}
static void video_cb(const void* data, unsigned w, unsigned h, size_t pitch) {
  if (!data || data==(const void*)(intptr_t)-1 || !w || !h) return;
  std::lock_guard<std::mutex> lk(g_frameMu);
  g_w=w; g_h=h; g_frame.resize((size_t)w*h);
  if (g_pixelFmt==RETRO_PIXEL_FORMAT_XRGB8888) {
    for(unsigned y=0;y<h;y++) {
      auto* s=(const uint32_t*)((const uint8_t*)data+y*pitch);
      for(unsigned x=0;x<w;x++) g_frame[(size_t)y*w+x]=0xFF000000u|(s[x]&0x00FFFFFFu);
    }
  } else {
    for(unsigned y=0;y<h;y++) {
      auto* s=(const uint16_t*)((const uint8_t*)data+y*pitch);
      for(unsigned x=0;x<w;x++) g_frame[(size_t)y*w+x]=(g_pixelFmt==RETRO_PIXEL_FORMAT_RGB565)?rgb565(s[x]):rgb1555(s[x]);
    }
  }
}
static void audio_one(int16_t l,int16_t r) {
  std::lock_guard<std::mutex> lk(g_audioMu);
  g_audio.push_back(l); g_audio.push_back(r); g_audioGeneratedSamples.fetch_add(2,std::memory_order_relaxed);
}
static size_t audio_batch(const int16_t* p,size_t frames) {
  std::lock_guard<std::mutex> lk(g_audioMu);
  size_t samples=frames*2, maxSamples=131072;
  for(size_t i=0;i<samples;i++) g_audio.push_back(p[i]);
  g_audioGeneratedSamples.fetch_add(samples,std::memory_order_relaxed);
  while(g_audio.size()>maxSamples) { g_audio.pop_front(); g_audioDroppedSamples.fetch_add(1,std::memory_order_relaxed); }
  return frames;
}
static void input_poll() {}
static int16_t input_state(unsigned port,unsigned device,unsigned index,unsigned id) {
  (void)index; if(port!=0 || device!=RETRO_DEVICE_JOYPAD) return 0;
  uint32_t m=g_input.load(std::memory_order_relaxed);
  if(id==RETRO_DEVICE_ID_JOYPAD_MASK) return (int16_t)m;
  return id<16 ? ((m>>id)&1u) : 0;
}

template<typename T> static bool sym(T& out,const char* n) {
  out=reinterpret_cast<T>(dlsym(g.so,n)); if(!out){ g_lastError=std::string("missing symbol: ")+n; return false;} return true;
}
static void close_core() {
  if(g_loaded.exchange(false)) { if(g.unload_game) g.unload_game(); }
  if(g_initialized && g.deinit) g.deinit();
  g_initialized=false;
  if(g.so) dlclose(g.so);
  g=Core{}; g_rom.clear();
}
static bool open_core(const std::string& libDir) {
  close_core();
  std::string p=libDir+"/libmgba_libretro.so";
  g.so=dlopen(p.c_str(),RTLD_NOW|RTLD_LOCAL);
  if(!g.so){ const char* err=dlerror(); g_lastError=err?err:"dlopen failed"; return false; }
  if(!sym(g.set_environment,"retro_set_environment") || !sym(g.set_video_refresh,"retro_set_video_refresh") ||
     !sym(g.set_audio_sample,"retro_set_audio_sample") || !sym(g.set_audio_sample_batch,"retro_set_audio_sample_batch") ||
     !sym(g.set_input_poll,"retro_set_input_poll") || !sym(g.set_input_state,"retro_set_input_state") ||
     !sym(g.init,"retro_init") || !sym(g.deinit,"retro_deinit") || !sym(g.load_game,"retro_load_game") ||
     !sym(g.unload_game,"retro_unload_game") || !sym(g.run,"retro_run") || !sym(g.reset,"retro_reset") ||
     !sym(g.get_system_av_info,"retro_get_system_av_info") || !sym(g.get_memory_data,"retro_get_memory_data") ||
     !sym(g.get_memory_size,"retro_get_memory_size")) { close_core(); return false; }
  g.set_environment(env_cb); g.set_video_refresh(video_cb); g.set_audio_sample(audio_one); g.set_audio_sample_batch(audio_batch);
  g.set_input_poll(input_poll); g.set_input_state(input_state); g.init(); g_initialized=true; return true;
}
static bool read_file(const std::string& p,std::vector<uint8_t>& out) {
  std::ifstream f(p,std::ios::binary|std::ios::ate); if(!f) return false;
  auto n=f.tellg(); if(n<=0 || n>128*1024*1024) return false; out.resize((size_t)n); f.seekg(0); f.read((char*)out.data(),n); return !!f;
}
static bool save_sram(const std::string& path) {
  if(!g_loaded || !g.get_memory_size || !g.get_memory_data) return false;
  size_t n=g.get_memory_size(0); void* p=g.get_memory_data(0); if(!n || !p) return false;
  std::ofstream f(path,std::ios::binary|std::ios::trunc); if(!f) return false; f.write((char*)p,n); return !!f;
}
static bool load_sram(const std::string& path) {
  if(!g_loaded || !g.get_memory_size || !g.get_memory_data) return false;
  size_t n=g.get_memory_size(0); void* p=g.get_memory_data(0); if(!n || !p) return false;
  std::ifstream f(path,std::ios::binary); if(!f) return false; f.read((char*)p,n); return f.gcount()>0;
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeInit(JNIEnv* e,jclass,jstring lib,jstring files) {
  const char* a=e->GetStringUTFChars(lib,nullptr); const char* b=e->GetStringUTFChars(files,nullptr);
  std::string ld=a, fd=b; e->ReleaseStringUTFChars(lib,a); e->ReleaseStringUTFChars(files,b);
  g_systemDir=fd; g_saveDir=fd; g_lastError.clear(); return open_core(ld)?JNI_TRUE:JNI_FALSE;
}
extern "C" JNIEXPORT jboolean JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeLoadRom(JNIEnv* e,jclass,jstring rom,jstring save) {
  const char* rp=e->GetStringUTFChars(rom,nullptr); const char* sp=e->GetStringUTFChars(save,nullptr);
  std::string r=rp,s=sp; e->ReleaseStringUTFChars(rom,rp); e->ReleaseStringUTFChars(save,sp);
  if(g_loaded.exchange(false) && g.unload_game) g.unload_game();
  if(!read_file(r,g_rom)){ g_lastError="ROM read failed"; return JNI_FALSE; }
  retro_game_info info{r.c_str(),g_rom.data(),g_rom.size(),nullptr};
  if(!g.load_game(&info)){ g_lastError="mGBA retro_load_game failed"; return JNI_FALSE; }
  g_loaded=true; retro_system_av_info av{}; g.get_system_av_info(&av); g_fps=av.timing.fps; g_sampleRate=av.timing.sample_rate;
  g_audioGeneratedSamples=0; g_audioDrainedSamples=0; g_audioDroppedSamples=0;
  { std::lock_guard<std::mutex> lk(g_audioMu); g_audio.clear(); }
  load_sram(s); LOGI("ROM loaded bytes=%zu fps=%.6f audio=%.1f",g_rom.size(),g_fps,g_sampleRate); return JNI_TRUE;
}
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeRunFrame(JNIEnv*,jclass){ if(g_loaded && g.run) g.run(); }
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeCopyFrame(JNIEnv* e,jclass,jintArray arr){
  std::lock_guard<std::mutex> lk(g_frameMu); jsize n=e->GetArrayLength(arr); size_t need=g_frame.size(); if((size_t)n<need) return -(jint)need;
  if(need) e->SetIntArrayRegion(arr,0,(jsize)need,(const jint*)g_frame.data()); return (jint)((g_w<<16)|(g_h&0xFFFF));
}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeDrainAudio(JNIEnv* e,jclass,jshortArray arr){
  std::lock_guard<std::mutex> lk(g_audioMu); jsize cap=e->GetArrayLength(arr); int n=(int)std::min<size_t>((size_t)cap,g_audio.size());
  if(!n) return 0; std::vector<jshort> tmp(n); for(int i=0;i<n;i++){tmp[i]=g_audio.front();g_audio.pop_front();} e->SetShortArrayRegion(arr,0,n,tmp.data()); g_audioDrainedSamples.fetch_add((uint64_t)n,std::memory_order_relaxed); return n;
}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeAudioQueueSamples(JNIEnv*,jclass){ std::lock_guard<std::mutex> lk(g_audioMu); return (jint)g_audio.size(); }
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeAudioGeneratedSamples(JNIEnv*,jclass){ return (jlong)g_audioGeneratedSamples.load(); }
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeAudioDrainedSamples(JNIEnv*,jclass){ return (jlong)g_audioDrainedSamples.load(); }
extern "C" JNIEXPORT jlong JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeAudioDroppedSamples(JNIEnv*,jclass){ return (jlong)g_audioDroppedSamples.load(); }
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeSetInputMask(JNIEnv*,jclass,jint m){ g_input=(uint32_t)m; }
extern "C" JNIEXPORT jdouble JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeFps(JNIEnv*,jclass){ return g_fps; }
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeSampleRate(JNIEnv*,jclass){ return (jint)(g_sampleRate+0.5); }
extern "C" JNIEXPORT jboolean JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeSaveSram(JNIEnv* e,jclass,jstring save){ const char* s=e->GetStringUTFChars(save,nullptr); bool ok=save_sram(s); e->ReleaseStringUTFChars(save,s); return ok?JNI_TRUE:JNI_FALSE; }
extern "C" JNIEXPORT jstring JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeLastError(JNIEnv* e,jclass){ return e->NewStringUTF(g_lastError.c_str()); }
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeReset(JNIEnv*,jclass){ if(g_loaded&&g.reset)g.reset(); }
extern "C" JNIEXPORT void JNICALL Java_com_showpei_soulgold_m6a2_MainActivity_nativeShutdown(JNIEnv*,jclass){ close_core(); }
