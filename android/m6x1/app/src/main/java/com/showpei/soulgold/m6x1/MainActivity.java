package com.showpei.soulgold.m6x1;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTimestamp;
import android.media.AudioTrack;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Process;
import android.os.SystemClock;
import android.provider.OpenableColumns;
import android.view.Choreographer;
import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.locks.LockSupport;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public final class MainActivity extends Activity {
    static { System.loadLibrary("soulgold_m6x1"); }

    private static final int PICK_PACK=6101, PICK_ROM=6102;
    private static final long EXACT_ROM_BYTES=33554432L;
    private static final int RID_B=0, RID_SELECT=2, RID_START=3, RID_UP=4, RID_DOWN=5,
            RID_LEFT=6, RID_RIGHT=7, RID_A=8, RID_L=10, RID_R=11;

    static native boolean nativeInit(String nativeLibraryDir,String filesDir);
    static native boolean nativeLoadRom(String romPath,String savePath);
    static native void nativeSetBackProviders(int[] species);
    static native void nativeRunFrame();
    static native int nativeCopyFrame(int[] outPixels);
    static native int nativeGetPlayerProxy(int[] out);
    static native int nativeDrainAudio(short[] outSamples);
    static native int nativeAudioQueueSamples();
    static native long nativeAudioGeneratedSamples();
    static native long nativeAudioDrainedSamples();
    static native long nativeAudioDroppedSamples();
    static native void nativeSetInputMask(int mask);
    static native double nativeFps();
    static native int nativeReportedSampleRate();
    static native int nativeEffectiveSampleRate();
    static native int nativeBridgeAddress();
    static native long nativeRegistryAttempts();
    static native long nativeRegistrySyncs();
    static native long nativeRegistryFailures();
    static native int nativeLastRomMagic();
    static native int nativeLastBridgeVersion();
    static native int nativeLastHostReadback();
    static native int nativeLastBackCountReadback();
    static native int nativeLastBridgeError();
    static native boolean nativeBridgeFresh();
    static native boolean nativeSaveSram(String savePath);
    static native String nativeLastError();
    static native void nativeReset();
    static native void nativeShutdown();

    private RuntimeView gameView;
    private Button packButton,romButton;
    private TextView status;
    private File saveFile,packDir;
    private int inputMask;
    private String romName="",romSha256="",packName="",packId="",packExpectedRomSha="";
    private long romBytes;
    private final Map<Integer,Provider> providers=new HashMap<>();

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        enterImmersive();
        File saves=new File(getFilesDir(),"saves");saves.mkdirs();
        saveFile=new File(saves,"soulgold_m6x1.sav");
        packDir=new File(getFilesDir(),"external_pack");

        FrameLayout root=new FrameLayout(this);
        gameView=new RuntimeView();root.addView(gameView,new FrameLayout.LayoutParams(-1,-1));
        packButton=new Button(this);packButton.setText("1. 匯入 Showdown 外部資源包");packButton.setTextSize(17f);packButton.setOnClickListener(v->choose(PICK_PACK));
        FrameLayout.LayoutParams p1=new FrameLayout.LayoutParams(-2,-2);p1.leftMargin=42;p1.topMargin=145;root.addView(packButton,p1);
        romButton=new Button(this);romButton.setText("2. 選擇配對的 32 MiB SoulGold ROM");romButton.setTextSize(17f);romButton.setEnabled(false);romButton.setOnClickListener(v->choose(PICK_ROM));
        FrameLayout.LayoutParams p2=new FrameLayout.LayoutParams(-2,-2);p2.leftMargin=42;p2.topMargin=220;root.addView(romButton,p2);
        status=new TextView(this);status.setTextColor(Color.WHITE);status.setTextSize(15f);status.setBackgroundColor(0xBB101418);status.setPadding(16,10,16,10);
        FrameLayout.LayoutParams sp=new FrameLayout.LayoutParams(-2,-2);sp.leftMargin=18;sp.topMargin=18;root.addView(status,sp);setContentView(root);

        boolean ok=nativeInit(getApplicationInfo().nativeLibraryDir,getFilesDir().getAbsolutePath());
        if(!ok){status.setText("M6X1 native/mGBA 初始化失敗："+nativeLastError());packButton.setEnabled(false);}
        else status.setText("SoulGold M6X1 · Registry Runtime Bridge + 65536 Hz Audio Authority\n先匯入 SGXP，再選本版 32 MiB ROM。");
    }

    @Override protected void onResume(){super.onResume();enterImmersive();gameView.resumeLoop();}
    @Override protected void onPause(){gameView.pauseLoop();saveNow();super.onPause();}
    @Override protected void onDestroy(){gameView.shutdownRuntime();nativeShutdown();for(Provider p:providers.values())p.recycle();super.onDestroy();}
    @Override public void onWindowFocusChanged(boolean focus){super.onWindowFocusChanged(focus);if(focus)enterImmersive();}
    private void enterImmersive(){getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY|View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_LAYOUT_STABLE);}
    private void choose(int req){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("*/*");startActivityForResult(i,req);}

    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);if(result!=RESULT_OK||data==null||data.getData()==null)return;
        try{
            if(request==PICK_PACK)importPack(data.getData());
            else if(request==PICK_ROM)importRom(data.getData());
        }catch(Exception ex){status.setVisibility(View.VISIBLE);status.setText("M6X1 匯入失敗："+ex.getMessage());}
    }

    private void importPack(Uri uri)throws Exception{
        String display=queryName(uri);if(display!=null&&!display.toLowerCase(Locale.ROOT).endsWith(".sgxp"))throw new Exception("請選 .sgxp，選到："+display);
        deleteTree(packDir);packDir.mkdirs();
        int entries=0;long total=0;
        try(InputStream raw=getContentResolver().openInputStream(uri);ZipInputStream zin=new ZipInputStream(new BufferedInputStream(raw))){
            if(raw==null)throw new Exception("無法開啟 SGXP URI");ZipEntry ze;byte[]buf=new byte[1<<16];
            while((ze=zin.getNextEntry())!=null){
                if(++entries>5000)throw new Exception("SGXP 項目過多");String name=ze.getName().replace('\\','/');
                if(name.startsWith("/")||name.contains("../"))throw new Exception("SGXP 路徑越界："+name);
                File out=new File(packDir,name);String root=packDir.getCanonicalPath()+File.separator;if(!out.getCanonicalPath().startsWith(root)&&!out.getCanonicalPath().equals(packDir.getCanonicalPath()))throw new Exception("SGXP 路徑越界");
                if(ze.isDirectory()){out.mkdirs();continue;}File parent=out.getParentFile();if(parent!=null)parent.mkdirs();
                try(FileOutputStream fos=new FileOutputStream(out)){int n;while((n=zin.read(buf))>0){total+=n;if(total>256L*1024*1024)throw new Exception("SGXP 解壓超過 256 MiB");fos.write(buf,0,n);}}
            }
        }
        File mf=new File(packDir,"manifest.json");if(!mf.isFile())throw new Exception("缺少 manifest.json");
        JSONObject m=new JSONObject(readText(mf));if(!"SOULGOLD_SHOWDOWN_PACK_V1".equals(m.optString("format")))throw new Exception("不支援的資源包格式");
        packId=m.getString("pack_id");packExpectedRomSha=m.getString("expected_rom_sha256").toLowerCase(Locale.ROOT);packName=display==null?"M6X1.sgxp":display;
        providers.clear();JSONArray arr=m.getJSONArray("back_providers");
        for(int i=0;i<arr.length();i++){
            JSONObject o=arr.getJSONObject(i);Provider p=new Provider();p.species=o.getInt("species");p.name=o.optString("name","species_"+p.species);p.scale=(float)o.optDouble("scale",1.0);
            JSONArray fs=o.getJSONArray("frames");for(int k=0;k<fs.length();k++){JSONObject f=fs.getJSONObject(k);File img=new File(packDir,f.getString("path"));if(!img.isFile())throw new Exception("缺少 frame："+f.getString("path"));p.frames.add(new AnimFrame(img,Math.max(20,f.optInt("duration_ms",100))));}
            if(p.frames.isEmpty())throw new Exception("provider 無 frame："+p.name);providers.put(p.species,p);
        }
        int[] ids=new int[providers.size()];int q=0;for(int id:providers.keySet())ids[q++]=id;nativeSetBackProviders(ids);
        romButton.setEnabled(!providers.isEmpty());status.setVisibility(View.VISIBLE);status.setText("M6X1 SGXP 驗證成功 · BACK providers="+providers.size()+"\npack="+packId+"\n接著選配對 ROM。");
    }

    private void importRom(Uri uri)throws Exception{
        if(providers.isEmpty())throw new Exception("請先匯入 SGXP");String display=queryName(uri);if(display!=null&&!display.toLowerCase(Locale.ROOT).endsWith(".gba"))throw new Exception("請選 .gba");
        File romDir=new File(getFilesDir(),"roms");romDir.mkdirs();File out=new File(romDir,"soulgold_m6x1.gba");MessageDigest sha=MessageDigest.getInstance("SHA-256");long total=0;
        try(InputStream in=getContentResolver().openInputStream(uri);FileOutputStream fos=new FileOutputStream(out)){if(in==null)throw new Exception("無法開啟 ROM URI");byte[]buf=new byte[1<<16];int n;while((n=in.read(buf))>0){fos.write(buf,0,n);sha.update(buf,0,n);total+=n;if(total>EXACT_ROM_BYTES)throw new Exception("ROM 超過 32 MiB");}}
        if(total!=EXACT_ROM_BYTES)throw new Exception("ROM 必須剛好 33,554,432 bytes，目前 "+total);
        String digest=hex(sha.digest());if(!digest.equalsIgnoreCase(packExpectedRomSha))throw new Exception("ROM / SGXP SHA 不配對\nROM="+digest+"\nPACK expects="+packExpectedRomSha);
        romName=display==null?"SoulGold_M6X1.gba":display;romBytes=total;romSha256=digest;
        gameView.stopWorkers();if(!nativeLoadRom(out.getAbsolutePath(),saveFile.getAbsolutePath()))throw new Exception(nativeLastError());
        int[] ids=new int[providers.size()];int q=0;for(int id:providers.keySet())ids[q++]=id;nativeSetBackProviders(ids);
        gameView.startRuntime();packButton.setVisibility(View.GONE);romButton.setVisibility(View.GONE);status.setVisibility(View.VISIBLE);
        status.setText(String.format(Locale.US,"M6X1 ACTIVE · core %.4f FPS\nAudio reported %d Hz → effective %d Hz → device %d Hz\nbridge=0x%08X · BACK=%d",nativeFps(),nativeReportedSampleRate(),nativeEffectiveSampleRate(),gameView.nativeOutputRate,nativeBridgeAddress(),providers.size()));
        status.postDelayed(()->status.setVisibility(View.GONE),8000);
    }

    private String queryName(Uri uri){try(Cursor c=getContentResolver().query(uri,null,null,null,null)){if(c!=null&&c.moveToFirst()){int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);if(i>=0)return c.getString(i);}}catch(Exception ignored){}return null;}
    private static String readText(File f)throws Exception{try(FileInputStream in=new FileInputStream(f)){byte[]b=new byte[(int)f.length()];int off=0,n;while(off<b.length&&(n=in.read(b,off,b.length-off))>0)off+=n;return new String(b,0,off,StandardCharsets.UTF_8);}}
    private static String hex(byte[]b){StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format(Locale.US,"%02x",x&255));return s.toString();}
    private static String hex32(int x){return String.format(Locale.US,"0x%08X",x);}
    private static void deleteTree(File f){if(f==null||!f.exists())return;if(f.isDirectory()){File[]a=f.listFiles();if(a!=null)for(File x:a)deleteTree(x);}f.delete();}
    private boolean gameDevice(InputDevice d){if(d==null)return false;int s=d.getSources();return(s&InputDevice.SOURCE_GAMEPAD)==InputDevice.SOURCE_GAMEPAD||(s&InputDevice.SOURCE_JOYSTICK)==InputDevice.SOURCE_JOYSTICK;}
    private int retroId(int code){switch(code){case KeyEvent.KEYCODE_BUTTON_A:return RID_A;case KeyEvent.KEYCODE_BUTTON_B:return RID_B;case KeyEvent.KEYCODE_BUTTON_L1:return RID_L;case KeyEvent.KEYCODE_BUTTON_R1:return RID_R;case KeyEvent.KEYCODE_BUTTON_START:return RID_START;case KeyEvent.KEYCODE_BUTTON_SELECT:case KeyEvent.KEYCODE_BACK:return RID_SELECT;case KeyEvent.KEYCODE_DPAD_UP:return RID_UP;case KeyEvent.KEYCODE_DPAD_DOWN:return RID_DOWN;case KeyEvent.KEYCODE_DPAD_LEFT:return RID_LEFT;case KeyEvent.KEYCODE_DPAD_RIGHT:return RID_RIGHT;default:return-1;}}
    @Override public boolean dispatchKeyEvent(KeyEvent e){if(gameDevice(e.getDevice())){int id=retroId(e.getKeyCode());if(id>=0){if(e.getAction()==KeyEvent.ACTION_DOWN)inputMask|=1<<id;else if(e.getAction()==KeyEvent.ACTION_UP)inputMask&=~(1<<id);nativeSetInputMask(inputMask);if((inputMask&(1<<RID_L))!=0&&(inputMask&(1<<RID_R))!=0&&(inputMask&(1<<RID_START))!=0)gameView.requestReset();if((inputMask&(1<<RID_START))!=0&&(inputMask&(1<<RID_SELECT))!=0)writeReport("start_select");return true;}}return super.dispatchKeyEvent(e);}
    @Override public boolean dispatchGenericMotionEvent(MotionEvent e){if(gameDevice(e.getDevice())&&e.getAction()==MotionEvent.ACTION_MOVE){float x=e.getAxisValue(MotionEvent.AXIS_X),y=e.getAxisValue(MotionEvent.AXIS_Y);int m=inputMask;m&=~((1<<RID_LEFT)|(1<<RID_RIGHT)|(1<<RID_UP)|(1<<RID_DOWN));if(x<-.5f)m|=1<<RID_LEFT;else if(x>.5f)m|=1<<RID_RIGHT;if(y<-.5f)m|=1<<RID_UP;else if(y>.5f)m|=1<<RID_DOWN;inputMask=m;nativeSetInputMask(m);return true;}return super.dispatchGenericMotionEvent(e);}
    private void saveNow(){if(gameView.loaded)nativeSaveSram(saveFile.getAbsolutePath());}

    private void writeReport(String reason){
        try{
            JSONObject j=new JSONObject();j.put("milestone","M6X1_REGISTRY_AUDIO_FIX");j.put("reason",reason);j.put("manufacturer",Build.MANUFACTURER);j.put("model",Build.MODEL);j.put("sdk",Build.VERSION.SDK_INT);
            JSONArray abis=new JSONArray();for(String a:Build.SUPPORTED_ABIS)abis.put(a);j.put("abis",abis);j.put("rom_name",romName);j.put("rom_bytes",romBytes);j.put("rom_sha256",romSha256);j.put("main_rom_exact_32_mib",romBytes==EXACT_ROM_BYTES);
            j.put("external_pack_name",packName);j.put("external_pack_id",packId);j.put("external_pack_expected_rom_sha256",packExpectedRomSha);j.put("external_pack_native_back_providers",providers.size());
            j.put("external_registry_sync_attempts",nativeRegistryAttempts());j.put("external_registry_syncs",nativeRegistrySyncs());j.put("external_registry_failures",nativeRegistryFailures());j.put("external_bridge_address",hex32(nativeBridgeAddress()));j.put("external_bridge_rom_magic",hex32(nativeLastRomMagic()));j.put("external_bridge_version",nativeLastBridgeVersion());j.put("external_bridge_host_magic_readback",hex32(nativeLastHostReadback()));j.put("external_bridge_back_count_readback",nativeLastBackCountReadback());j.put("external_bridge_last_error",nativeLastBridgeError());j.put("external_bridge_fresh",nativeBridgeFresh());
            j.put("external_overlay_frames",gameView.overlayFrames);j.put("external_overlay_failures",gameView.overlayFailures);j.put("external_active_species",gameView.activeSpecies);
            j.put("core_reported_fps",nativeFps());j.put("source_reported_rate",nativeReportedSampleRate());j.put("source_effective_rate",nativeEffectiveSampleRate());j.put("native_output_rate",gameView.nativeOutputRate);j.put("audio_track_rate",gameView.audioTrackRate);j.put("audio_track_buffer_bytes",gameView.audioBufferBytes);j.put("audio_track_buffer_frames",gameView.audioBufferFrames);j.put("emu_frames",gameView.frames);j.put("display_callbacks",gameView.displayCallbacks);j.put("core_deadline_rebases",gameView.coreDeadlineRebases);j.put("core_max_late_ms",gameView.coreMaxLateNs/1_000_000.0);
            long generated=nativeAudioGeneratedSamples();j.put("audio_generated_source_samples",generated);j.put("audio_drained_source_samples",nativeAudioDrainedSamples());j.put("audio_dropped_source_samples",nativeAudioDroppedSamples());j.put("latency_recovery_dropped_source_samples",0);j.put("audio_written_output_samples",gameView.audioWrittenSamples);j.put("audio_write_errors",gameView.audioWriteErrors);j.put("native_audio_queue_samples",nativeAudioQueueSamples());j.put("source_queue_peak_samples",gameView.sourceQueuePeak);j.put("source_queue_target_samples",gameView.sourceQueueTargetShorts);j.put("source_queue_hard_samples",gameView.sourceQueueHardShorts);j.put("source_queue_over_hard_events",gameView.sourceQueueOverHardEvents);j.put("drc_rate_adjust_current",gameView.drcCurrent);j.put("drc_rate_adjust_min",gameView.drcMin);j.put("drc_rate_adjust_max",gameView.drcMax);
            double seconds=gameView.frames/Math.max(1.0,nativeFps());double observed=seconds>0?(generated/2.0)/seconds:0;j.put("source_observed_rate_from_core_frames",observed);
            long playback=gameView.playbackHeadFrames(),writtenFrames=gameView.audioWrittenSamples/2L,queuedFrames=Math.max(0,writtenFrames-playback);double queuedMs=gameView.audioTrackRate>0?1000.0*queuedFrames/gameView.audioTrackRate:0;j.put("playback_head_output_frames",playback);j.put("estimated_sink_queued_frames",queuedFrames);j.put("estimated_sink_latency_ms",queuedMs);j.put("audio_underrun_count",gameView.underrunCount());
            AudioTimestamp ts=gameView.audioTimestamp();if(ts!=null){j.put("audio_timestamp_frame_position",ts.framePosition);j.put("audio_timestamp_nano_time",ts.nanoTime);}
            j.put("core_clock_master","mgba_monotonic_fps");j.put("audio_rate_authority","effective_65536_from_pinned_runtime_and_thor_evidence");j.put("audio_feedback_drc",true);j.put("drc_limit_fraction",0.005);j.put("live_latency_sample_deletion",false);j.put("audio_sink_blocks_core",false);j.put("choreographer_advances_emulation",false);j.put("showdown_compositor_in_apk",true);j.put("showdown_assets_in_apk",false);j.put("external_pack_required",true);
            File base=getExternalFilesDir(null);if(base==null)base=getFilesDir();File diag=new File(base,"diagnostics");diag.mkdirs();File out=new File(diag,"M6X1_REGISTRY_AUDIO_REPORT.json");try(FileOutputStream f=new FileOutputStream(out)){f.write(j.toString(2).getBytes(StandardCharsets.UTF_8));}
            status.setVisibility(View.VISIBLE);status.setText("M6X1 診斷已輸出：\n"+out.getAbsolutePath());status.postDelayed(()->status.setVisibility(View.GONE),6000);
        }catch(Exception ignored){}
    }

    final class RuntimeView extends View implements Choreographer.FrameCallback{
        final Paint paint=new Paint();final Paint bootPaint=new Paint(Paint.ANTI_ALIAS_FLAG);final int[]pixels=new int[256*224];final int[]proxy=new int[10];final short[]sourceBuf=new short[4096];final short[]outputBuf=new short[8192];final LinearResampler resampler=new LinearResampler();
        Bitmap bmp;AudioTrack audio;volatile boolean loop,loaded,coreRun,audioRun,resetRequested;volatile long frames,displayCallbacks,audioWrittenSamples,audioWriteErrors,coreDeadlineRebases,coreMaxLateNs,sourceQueueOverHardEvents,overlayFrames,overlayFailures;volatile int sourceQueuePeak,activeSpecies;volatile double drcCurrent=1,drcMin=1,drcMax=1;Thread coreWorker,audioWorker;int nativeOutputRate,audioTrackRate,audioBufferBytes,audioBufferFrames,sourceQueueTargetShorts,sourceQueueHardShorts;long lastSave;
        RuntimeView(){super(MainActivity.this);paint.setFilterBitmap(false);bootPaint.setColor(Color.rgb(120,230,170));bootPaint.setTextSize(28f);setBackgroundColor(Color.BLACK);}
        void resumeLoop(){if(!loop){loop=true;Choreographer.getInstance().postFrameCallback(this);}if(loaded)startWorkers();}
        void pauseLoop(){loop=false;stopWorkers();discardNativeAudio();}
        void startRuntime(){loaded=true;frames=displayCallbacks=audioWrittenSamples=audioWriteErrors=coreDeadlineRebases=coreMaxLateNs=sourceQueueOverHardEvents=overlayFrames=overlayFailures=0;sourceQueuePeak=activeSpecies=0;drcCurrent=drcMin=drcMax=1;resetRequested=false;lastSave=SystemClock.elapsedRealtime();discardNativeAudio();initAudio();int src=nativeEffectiveSampleRate();double fps=Math.max(1,nativeFps());int oneFrameShorts=(int)Math.ceil(src/fps)*2;sourceQueueTargetShorts=Math.max(oneFrameShorts*2,2048);sourceQueueHardShorts=Math.max(sourceQueueTargetShorts*3,8192);resampler.reset(src,audioTrackRate);startWorkers();resumeLoop();invalidate();}
        void shutdownRuntime(){loop=false;stopWorkers();discardNativeAudio();closeAudio();loaded=false;}
        void requestReset(){if(loaded)resetRequested=true;}
        void initAudio(){closeAudio();nativeOutputRate=AudioTrack.getNativeOutputSampleRate(AudioManager.STREAM_MUSIC);if(nativeOutputRate<8000)nativeOutputRate=48000;int min=AudioTrack.getMinBufferSize(nativeOutputRate,AudioFormat.CHANNEL_OUT_STEREO,AudioFormat.ENCODING_PCM_16BIT);if(min<0)min=4096;int targetFrames=(int)Math.ceil(nativeOutputRate*.032);audioBufferBytes=Math.max(min,targetFrames*4);AudioAttributes attrs=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build();AudioFormat fmt=new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT).setSampleRate(nativeOutputRate).setChannelMask(AudioFormat.CHANNEL_OUT_STEREO).build();AudioTrack.Builder b=new AudioTrack.Builder().setAudioAttributes(attrs).setAudioFormat(fmt).setTransferMode(AudioTrack.MODE_STREAM).setBufferSizeInBytes(audioBufferBytes);if(Build.VERSION.SDK_INT>=26)b.setPerformanceMode(AudioTrack.PERFORMANCE_MODE_LOW_LATENCY);audio=b.build();audioTrackRate=audio.getSampleRate();audioBufferFrames=audio.getBufferSizeInFrames();}
        void closeAudio(){AudioTrack a=audio;audio=null;if(a!=null)try{a.pause();a.flush();a.release();}catch(Exception ignored){}}
        synchronized void startWorkers(){if(!loaded||audio==null||coreRun||audioRun)return;discardNativeAudio();resampler.reset(nativeEffectiveSampleRate(),audioTrackRate);audioRun=coreRun=true;audioWorker=new Thread(this::audioLoop,"SoulGold-M6X1-AudioSink");coreWorker=new Thread(this::coreLoop,"SoulGold-M6X1-CoreClock");audioWorker.start();coreWorker.start();}
        synchronized void stopWorkers(){coreRun=audioRun=false;AudioTrack a=audio;if(a!=null)try{a.pause();a.flush();}catch(Exception ignored){}Thread c=coreWorker,s=audioWorker;coreWorker=audioWorker=null;if(c!=null&&c!=Thread.currentThread())try{c.join(1500);}catch(InterruptedException x){Thread.currentThread().interrupt();}if(s!=null&&s!=Thread.currentThread())try{s.join(1500);}catch(InterruptedException x){Thread.currentThread().interrupt();}}
        void coreLoop(){Process.setThreadPriority(Process.THREAD_PRIORITY_DISPLAY);double fps=Math.max(1,nativeFps());long period=Math.max(1L,(long)(1_000_000_000.0/fps)),next=System.nanoTime();while(coreRun&&loaded){if(resetRequested){resetRequested=false;nativeReset();discardNativeAudio();resampler.reset(nativeEffectiveSampleRate(),audioTrackRate);next=System.nanoTime()+period;}long now=System.nanoTime(),wait=next-now;if(wait>0){LockSupport.parkNanos(wait);if(!coreRun)break;now=System.nanoTime();}else{long late=-wait;if(late>coreMaxLateNs)coreMaxLateNs=late;if(late>period*3){coreDeadlineRebases++;next=now;}}nativeRunFrame();frames++;next+=period;long t=SystemClock.elapsedRealtime();if(t-lastSave>5000){nativeSaveSram(saveFile.getAbsolutePath());lastSave=t;}}}
        void audioLoop(){Process.setThreadPriority(Process.THREAD_PRIORITY_AUDIO);AudioTrack a=audio;if(a==null)return;try{a.play();}catch(Exception ex){audioWriteErrors++;return;}while(audioRun&&loaded){int queued=nativeAudioQueueSamples();if(queued>sourceQueuePeak)sourceQueuePeak=queued;if(queued>sourceQueueHardShorts)sourceQueueOverHardEvents++;if(queued<=0){LockSupport.parkNanos(500_000);continue;}double direction=(sourceQueueTargetShorts-queued)/(double)Math.max(1,sourceQueueTargetShorts);direction=Math.max(-1,Math.min(1,direction));double adjust=1+.005*direction;drcCurrent=adjust;if(adjust<drcMin)drcMin=adjust;if(adjust>drcMax)drcMax=adjust;int n=nativeDrainAudio(sourceBuf);if(n<=0){LockSupport.parkNanos(250_000);continue;}int out=resampler.process(sourceBuf,n,outputBuf,adjust);int off=0;while(audioRun&&off<out){int w;try{w=a.write(outputBuf,off,out-off,AudioTrack.WRITE_BLOCKING);}catch(Exception ex){audioWriteErrors++;audioRun=false;break;}if(w>0){off+=w;audioWrittenSamples+=w;}else{audioWriteErrors++;audioRun=false;break;}}}}
        void discardNativeAudio(){while(nativeAudioQueueSamples()>0){int n=nativeDrainAudio(sourceBuf);if(n<=0)break;}}
        void copyLatestFrame(){int info=nativeCopyFrame(pixels);if(info<=0)return;int w=(info>>>16)&0xffff,h=info&0xffff;if(w<=0||h<=0)return;if(bmp==null||bmp.getWidth()!=w||bmp.getHeight()!=h)bmp=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);bmp.setPixels(pixels,0,w,0,0,w,h);}
        long playbackHeadFrames(){AudioTrack a=audio;return a==null?0:Integer.toUnsignedLong(a.getPlaybackHeadPosition());}
        int underrunCount(){AudioTrack a=audio;return a==null?0:a.getUnderrunCount();}
        AudioTimestamp audioTimestamp(){AudioTrack a=audio;if(a==null)return null;AudioTimestamp ts=new AudioTimestamp();try{return a.getTimestamp(ts)?ts:null;}catch(Exception ignored){return null;}}
        @Override public void doFrame(long ns){if(!loop)return;displayCallbacks++;if(loaded)copyLatestFrame();invalidate();Choreographer.getInstance().postFrameCallback(this);}
        @Override protected void onDraw(Canvas c){super.onDraw(c);if(bmp==null){c.drawText("M6X1 · External Showdown Bridge",42,105,bootPaint);c.drawText("registry + 65536 Hz audio authority",42,145,bootPaint);return;}float sx=getWidth()/(float)bmp.getWidth(),sy=getHeight()/(float)bmp.getHeight(),s=Math.min(sx,sy);int dw=Math.round(bmp.getWidth()*s),dh=Math.round(bmp.getHeight()*s),l=(getWidth()-dw)/2,t=(getHeight()-dh)/2;c.drawBitmap(bmp,null,new Rect(l,t,l+dw,t+dh),paint);if(nativeGetPlayerProxy(proxy)==1){int species=proxy[0];Provider p=providers.get(species);if(p==null){overlayFailures++;activeSpecies=0;return;}Bitmap frame=p.frameAt(SystemClock.uptimeMillis());if(frame==null){overlayFailures++;activeSpecies=species;return;}float cx=l+(proxy[2]+proxy[4])*s,cy=t+(proxy[3]+proxy[5])*s;float fw=frame.getWidth()*p.scale*s,fh=frame.getHeight()*p.scale*s;RectF dst=new RectF(cx-fw/2f,cy-fh/2f,cx+fw/2f,cy+fh/2f);c.drawBitmap(frame,null,dst,paint);overlayFrames++;activeSpecies=species;}else activeSpecies=0;}
    }

    static final class AnimFrame{final File file;final int duration;AnimFrame(File f,int d){file=f;duration=d;}}
    static final class Provider{int species;String name;float scale=1;final ArrayList<AnimFrame>frames=new ArrayList<>();int cacheIndex=-1;Bitmap cache;long total(){long t=0;for(AnimFrame f:frames)t+=f.duration;return Math.max(1,t);}Bitmap frameAt(long now){if(frames.isEmpty())return null;long p=now%total(),a=0;int idx=0;for(int i=0;i<frames.size();i++){a+=frames.get(i).duration;if(p<a){idx=i;break;}}if(idx!=cacheIndex||cache==null||cache.isRecycled()){if(cache!=null&&!cache.isRecycled())cache.recycle();cache=BitmapFactory.decodeFile(frames.get(idx).file.getAbsolutePath());cacheIndex=idx;}return cache;}void recycle(){if(cache!=null&&!cache.isRecycled())cache.recycle();cache=null;cacheIndex=-1;}}

    static final class LinearResampler{
        private int srcRate=65536,dstRate=48000;private double pos;private short prevL,prevR;private boolean havePrev;
        void reset(int src,int dst){srcRate=src>0?src:65536;dstRate=dst>0?dst:48000;pos=0;havePrev=false;prevL=prevR=0;}
        int process(short[]in,int shorts,short[]out,double rateAdjust){int frames=shorts/2;if(frames<=0)return 0;double adj=Math.max(.995,Math.min(1.005,rateAdjust)),step=srcRate/(dstRate*adj);if(!havePrev){prevL=in[0];prevR=in[1];havePrev=true;}int o=0;while(pos<frames&&o+1<out.length){int base=(int)Math.floor(pos);double frac=pos-base;short l0,r0,l1,r1;if(base==0){l0=prevL;r0=prevR;}else{int q=(base-1)*2;l0=in[q];r0=in[q+1];}int nx=base*2;if(nx+1<shorts){l1=in[nx];r1=in[nx+1];}else{l1=in[shorts-2];r1=in[shorts-1];}int l=(int)Math.round(l0+(l1-l0)*frac),r=(int)Math.round(r0+(r1-r0)*frac);out[o++]=(short)Math.max(Short.MIN_VALUE,Math.min(Short.MAX_VALUE,l));out[o++]=(short)Math.max(Short.MIN_VALUE,Math.min(Short.MAX_VALUE,r));pos+=step;}pos-=frames;prevL=in[shorts-2];prevR=in[shorts-1];return o;}
    }
}
