package com.showpei.soulgold.m6a2;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Process;
import android.os.SystemClock;
import android.provider.OpenableColumns;
import android.database.Cursor;
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

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

public final class MainActivity extends Activity {
    static { System.loadLibrary("soulgold_m6a2"); }

    private static final int PICK_ROM = 6202;
    private static final int RID_B=0, RID_SELECT=2, RID_START=3, RID_UP=4, RID_DOWN=5,
            RID_LEFT=6, RID_RIGHT=7, RID_A=8, RID_L=10, RID_R=11;

    static native boolean nativeInit(String nativeLibraryDir, String filesDir);
    static native boolean nativeLoadRom(String romPath, String savePath);
    static native void nativeRunFrame();
    static native int nativeCopyFrame(int[] outPixels);
    static native int nativeDrainAudio(short[] outSamples);
    static native int nativeAudioQueueSamples();
    static native long nativeAudioGeneratedSamples();
    static native long nativeAudioDrainedSamples();
    static native long nativeAudioDroppedSamples();
    static native void nativeSetInputMask(int mask);
    static native double nativeFps();
    static native int nativeSampleRate();
    static native boolean nativeSaveSram(String savePath);
    static native String nativeLastError();
    static native void nativeReset();
    static native void nativeShutdown();

    private RuntimeView gameView;
    private Button pickButton;
    private TextView status;
    private File saveFile;
    private int inputMask;
    private String romName="";
    private String romSha256="";
    private long romBytes;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        enterImmersive();

        File saves = new File(getFilesDir(), "saves"); saves.mkdirs();
        saveFile = new File(saves, "soulgold_runtime.sav");

        FrameLayout root = new FrameLayout(this);
        gameView = new RuntimeView();
        root.addView(gameView, new FrameLayout.LayoutParams(-1,-1));

        pickButton = new Button(this);
        pickButton.setText("選擇 SoulGold / GBA ROM");
        pickButton.setTextSize(18f);
        pickButton.setOnClickListener(v -> chooseRom());
        FrameLayout.LayoutParams bp = new FrameLayout.LayoutParams(-2,-2);
        bp.leftMargin=42; bp.topMargin=170;
        root.addView(pickButton,bp);

        status = new TextView(this);
        status.setTextColor(Color.WHITE); status.setTextSize(15f);
        status.setBackgroundColor(0xAA101418); status.setPadding(16,10,16,10);
        FrameLayout.LayoutParams sp = new FrameLayout.LayoutParams(-2,-2);
        sp.leftMargin=18; sp.topMargin=18;
        root.addView(status,sp);
        setContentView(root);

        boolean ok=nativeInit(getApplicationInfo().nativeLibraryDir,getFilesDir().getAbsolutePath());
        if(!ok) {
            status.setText("M6A2 FIX2 native/mGBA 初始化失敗："+nativeLastError());
            pickButton.setEnabled(false);
        } else {
            status.setText("SoulGold M6A2 FIX2 · Timing/Audio/Presentation Preservation\n請選擇你自己的 .gba 備份。\n核心時鐘與 Android 顯示刷新率已解耦；ROM 不包含在 APK。");
        }
    }

    @Override protected void onResume(){ super.onResume(); enterImmersive(); gameView.resumeRuntime(); }
    @Override protected void onPause(){ gameView.pauseRuntime(); saveNow(); super.onPause(); }
    @Override protected void onDestroy(){ gameView.shutdownRuntime(); nativeShutdown(); super.onDestroy(); }
    @Override public void onWindowFocusChanged(boolean focus){ super.onWindowFocusChanged(focus); if(focus) enterImmersive(); }

    private void enterImmersive(){
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY|View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    private void chooseRom(){
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE); i.setType("*/*");
        startActivityForResult(i,PICK_ROM);
    }

    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=PICK_ROM || result!=RESULT_OK || data==null || data.getData()==null) return;
        Uri uri=data.getData();
        try {
            String display=queryName(uri);
            if(display!=null && !display.toLowerCase(Locale.ROOT).endsWith(".gba")) {
                status.setText("拒絕：M6A2 FIX2 目前只接受 .gba。選到："+display); return;
            }
            File romDir=new File(getFilesDir(),"roms"); romDir.mkdirs();
            File out=new File(romDir,"soulgold_user.gba");
            MessageDigest sha=MessageDigest.getInstance("SHA-256"); long total=0;
            try(InputStream in=getContentResolver().openInputStream(uri); FileOutputStream fos=new FileOutputStream(out)){
                if(in==null) throw new Exception("無法開啟 ROM URI");
                byte[] buf=new byte[1<<16]; int n;
                while((n=in.read(buf))>0){ fos.write(buf,0,n); sha.update(buf,0,n); total+=n; if(total>128L*1024*1024) throw new Exception("ROM 過大"); }
            }
            if(total<1024*1024) throw new Exception("檔案太小，不像 GBA ROM");
            romName=display==null?"soulgold_user.gba":display; romBytes=total; romSha256=hex(sha.digest());
            status.setText("載入 mGBA ARM64 core…\n"+romName+" · "+total+" bytes\nSHA-256 "+romSha256.substring(0,16)+"…");
            if(!nativeLoadRom(out.getAbsolutePath(),saveFile.getAbsolutePath())) throw new Exception(nativeLastError());
            gameView.startRuntime(); pickButton.setVisibility(View.GONE);
            status.setText(String.format(Locale.US,
                "M6A2 FIX2 RUNTIME ACTIVE · core %.4f FPS · audio %d Hz\n%s · %d bytes\nCore/audio 已獨立於 display VSYNC；Start+Select 寫入 timing report。",
                nativeFps(),nativeSampleRate(),romName,romBytes));
            status.postDelayed(() -> status.setVisibility(View.GONE),7000);
        } catch(Exception ex){ status.setVisibility(View.VISIBLE); status.setText("ROM boot 失敗："+ex.getMessage()); }
    }

    private String queryName(Uri uri){
        try(Cursor c=getContentResolver().query(uri,null,null,null,null)){
            if(c!=null && c.moveToFirst()){ int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME); if(i>=0) return c.getString(i); }
        } catch(Exception ignored){} return null;
    }
    private static String hex(byte[] b){ StringBuilder s=new StringBuilder(); for(byte x:b)s.append(String.format(Locale.US,"%02x",x&255)); return s.toString(); }

    private boolean gameDevice(InputDevice d){ if(d==null)return false; int s=d.getSources(); return (s&InputDevice.SOURCE_GAMEPAD)==InputDevice.SOURCE_GAMEPAD || (s&InputDevice.SOURCE_JOYSTICK)==InputDevice.SOURCE_JOYSTICK; }
    private int retroId(int code){
        switch(code){
            case KeyEvent.KEYCODE_BUTTON_A:return RID_A; case KeyEvent.KEYCODE_BUTTON_B:return RID_B;
            case KeyEvent.KEYCODE_BUTTON_L1:return RID_L; case KeyEvent.KEYCODE_BUTTON_R1:return RID_R;
            case KeyEvent.KEYCODE_BUTTON_START:return RID_START;
            case KeyEvent.KEYCODE_BUTTON_SELECT: case KeyEvent.KEYCODE_BACK:return RID_SELECT;
            case KeyEvent.KEYCODE_DPAD_UP:return RID_UP; case KeyEvent.KEYCODE_DPAD_DOWN:return RID_DOWN;
            case KeyEvent.KEYCODE_DPAD_LEFT:return RID_LEFT; case KeyEvent.KEYCODE_DPAD_RIGHT:return RID_RIGHT;
            default:return -1;
        }
    }
    @Override public boolean dispatchKeyEvent(KeyEvent e){
        if(gameDevice(e.getDevice())){
            int id=retroId(e.getKeyCode());
            if(id>=0){
                if(e.getAction()==KeyEvent.ACTION_DOWN) inputMask|=1<<id; else if(e.getAction()==KeyEvent.ACTION_UP) inputMask&=~(1<<id);
                nativeSetInputMask(inputMask);
                if((inputMask&(1<<RID_L))!=0 && (inputMask&(1<<RID_R))!=0 && (inputMask&(1<<RID_START))!=0) nativeReset();
                if((inputMask&(1<<RID_START))!=0 && (inputMask&(1<<RID_SELECT))!=0) writeReport("start_select");
                return true;
            }
        }
        return super.dispatchKeyEvent(e);
    }
    @Override public boolean dispatchGenericMotionEvent(MotionEvent e){
        if(gameDevice(e.getDevice()) && e.getAction()==MotionEvent.ACTION_MOVE){
            float x=e.getAxisValue(MotionEvent.AXIS_X), y=e.getAxisValue(MotionEvent.AXIS_Y); int m=inputMask;
            m&=~((1<<RID_LEFT)|(1<<RID_RIGHT)|(1<<RID_UP)|(1<<RID_DOWN));
            if(x<-0.5f)m|=1<<RID_LEFT; else if(x>0.5f)m|=1<<RID_RIGHT;
            if(y<-0.5f)m|=1<<RID_UP; else if(y>0.5f)m|=1<<RID_DOWN;
            inputMask=m; nativeSetInputMask(m); return true;
        }
        return super.dispatchGenericMotionEvent(e);
    }

    private void saveNow(){ if(gameView.loaded) nativeSaveSram(saveFile.getAbsolutePath()); }
    private void writeReport(String reason){
        try{
            JSONObject j=new JSONObject(); j.put("milestone","M6A2_FIX2"); j.put("probe","TIMING_AUDIO_NATIVE_PRESENTATION_PRESERVATION"); j.put("reason",reason);
            j.put("manufacturer",Build.MANUFACTURER); j.put("model",Build.MODEL); j.put("sdk",Build.VERSION.SDK_INT);
            JSONArray a=new JSONArray(); for(String abi:Build.SUPPORTED_ABIS)a.put(abi); j.put("abis",a);
            j.put("rom_name",romName); j.put("rom_bytes",romBytes); j.put("rom_sha256",romSha256);
            j.put("core_reported_fps",nativeFps()); j.put("audio_rate",nativeSampleRate());
            j.put("emu_frames",gameView.emuFrames.get()); j.put("display_callbacks",gameView.displayCallbacks.get());
            j.put("display_fps",gameView.renderFps); j.put("audio_generated_samples",nativeAudioGeneratedSamples());
            j.put("audio_drained_samples",nativeAudioDrainedSamples()); j.put("audio_dropped_samples",nativeAudioDroppedSamples());
            j.put("audio_written_samples",gameView.audioWrittenSamples.get()); j.put("audio_partial_writes",gameView.audioPartialWrites.get());
            j.put("audio_write_errors",gameView.audioWriteErrors.get()); j.put("audio_queue_samples",nativeAudioQueueSamples());
            j.put("core_clock_decoupled_from_vsync",true); j.put("audio_blocking_consumer",true);
            j.put("native_ui_animation_preservation_required",true); j.put("showdown_overlay_in_apk",false);
            j.put("rules",new JSONArray().put("R-SD-144").put("R-SD-145").put("R-SD-146").put("R-SD-147").put("R-SD-148"));
            File base=getExternalFilesDir(null); if(base==null)base=getFilesDir(); File out=new File(base,"M6A2_FIX2_TIMING_AUDIO_REPORT.json");
            try(FileOutputStream f=new FileOutputStream(out)){f.write(j.toString(2).getBytes(StandardCharsets.UTF_8));}
        }catch(Exception ignored){}
    }

    final class RuntimeView extends View implements Choreographer.FrameCallback {
        final Paint p=new Paint(); final Paint bootPaint=new Paint(Paint.ANTI_ALIAS_FLAG);
        final int[] pixels=new int[256*224]; Bitmap bmp;
        final AtomicBoolean running=new AtomicBoolean(false), audioRunning=new AtomicBoolean(false);
        final AtomicLong emuFrames=new AtomicLong(), displayCallbacks=new AtomicLong();
        final AtomicLong audioWrittenSamples=new AtomicLong(), audioPartialWrites=new AtomicLong(), audioWriteErrors=new AtomicLong();
        volatile boolean loaded; volatile float renderFps;
        volatile Thread emuThread,audioThread; volatile AudioTrack audio;
        long lastSaveMs; long lastDisplayNs; int displayFrames;

        RuntimeView(){ super(MainActivity.this); p.setFilterBitmap(false); bootPaint.setColor(Color.rgb(120,230,170)); bootPaint.setTextSize(30f); setBackgroundColor(Color.BLACK); }

        void startRuntime(){
            loaded=true; emuFrames.set(0); displayCallbacks.set(0); audioWrittenSamples.set(0); audioPartialWrites.set(0); audioWriteErrors.set(0);
            lastSaveMs=SystemClock.elapsedRealtime(); startWorkers(); resumeDisplay(); invalidate();
        }
        void resumeRuntime(){ if(loaded) startWorkers(); resumeDisplay(); }
        void pauseRuntime(){ stopWorkers(); pauseDisplay(); }
        void shutdownRuntime(){ stopWorkers(); pauseDisplay(); closeAudio(); }

        void startWorkers(){
            if(!loaded || running.getAndSet(true)) return;
            startAudio();
            emuThread=new Thread(() -> {
                Process.setThreadPriority(Process.THREAD_PRIORITY_DISPLAY);
                final double fps=Math.max(1.0,nativeFps());
                final long step=(long)(1_000_000_000.0/fps);
                long next=System.nanoTime();
                while(running.get()){
                    long now=System.nanoTime();
                    long wait=next-now;
                    if(wait>2_000_000L){
                        try{ long sleepNs=wait-1_000_000L; long ms=sleepNs/1_000_000L; int nsPart=(int)(sleepNs%1_000_000L); Thread.sleep(ms,nsPart); }catch(InterruptedException ignored){}
                        continue;
                    }
                    if(wait>0){ Thread.yield(); continue; }
                    nativeRunFrame(); emuFrames.incrementAndGet();
                    next+=step;
                    if(now-next>step*4) next=now+step;
                    long ms=SystemClock.elapsedRealtime();
                    if(ms-lastSaveMs>5000){ nativeSaveSram(saveFile.getAbsolutePath()); lastSaveMs=ms; }
                }
            },"SoulGold-M6A2-Emu");
            emuThread.start();
        }
        void stopWorkers(){
            if(!running.getAndSet(false)) return;
            audioRunning.set(false);
            Thread e=emuThread,a=audioThread; emuThread=null; audioThread=null;
            if(e!=null)e.interrupt(); if(a!=null)a.interrupt();
            try{ if(e!=null)e.join(500); }catch(InterruptedException ignored){}
            try{ if(a!=null)a.join(500); }catch(InterruptedException ignored){}
            if(audio!=null){ try{audio.pause();audio.flush();}catch(Exception ignored){} }
        }
        void startAudio(){
            closeAudio();
            int sr=nativeSampleRate(); if(sr<8000)sr=32768;
            int min=AudioTrack.getMinBufferSize(sr,AudioFormat.CHANNEL_OUT_STEREO,AudioFormat.ENCODING_PCM_16BIT);
            AudioAttributes attrs=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build();
            AudioFormat fmt=new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT).setSampleRate(sr).setChannelMask(AudioFormat.CHANNEL_OUT_STEREO).build();
            int bytes=Math.max(min*4,32768);
            audio=new AudioTrack(attrs,fmt,bytes,AudioTrack.MODE_STREAM,AudioManager.AUDIO_SESSION_ID_GENERATE);
            audio.play(); audioRunning.set(true);
            final short[] buf=new short[8192];
            audioThread=new Thread(() -> {
                Process.setThreadPriority(Process.THREAD_PRIORITY_AUDIO);
                while(audioRunning.get()){
                    int n=nativeDrainAudio(buf);
                    if(n<=0){ try{Thread.sleep(1);}catch(InterruptedException ignored){} continue; }
                    int off=0;
                    while(off<n && audioRunning.get()){
                        int remain=n-off;
                        int wrote=audio.write(buf,off,remain,AudioTrack.WRITE_BLOCKING);
                        if(wrote>0){ if(wrote<remain)audioPartialWrites.incrementAndGet(); off+=wrote; audioWrittenSamples.addAndGet(wrote); }
                        else { audioWriteErrors.incrementAndGet(); if(wrote<0) break; }
                    }
                }
            },"SoulGold-M6A2-Audio");
            audioThread.start();
        }
        void closeAudio(){ AudioTrack a=audio; audio=null; if(a!=null){try{a.pause();a.flush();a.release();}catch(Exception ignored){}} }

        void resumeDisplay(){ Choreographer.getInstance().removeFrameCallback(this); Choreographer.getInstance().postFrameCallback(this); }
        void pauseDisplay(){ Choreographer.getInstance().removeFrameCallback(this); }
        @Override public void doFrame(long ns){
            displayCallbacks.incrementAndGet();
            if(lastDisplayNs==0)lastDisplayNs=ns; displayFrames++;
            if(ns-lastDisplayNs>=1_000_000_000L){renderFps=(float)(displayFrames*1e9/(ns-lastDisplayNs));displayFrames=0;lastDisplayNs=ns;}
            if(loaded){
                int info=nativeCopyFrame(pixels);
                if(info>0){ int w=(info>>>16)&0xffff,h=info&0xffff; if(w>0&&h>0){ if(bmp==null||bmp.getWidth()!=w||bmp.getHeight()!=h)bmp=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888); bmp.setPixels(pixels,0,w,0,0,w,h); invalidate(); } }
            }
            Choreographer.getInstance().postFrameCallback(this);
        }
        @Override protected void onDraw(Canvas c){ super.onDraw(c); if(bmp!=null){float sx=getWidth()/(float)bmp.getWidth(),sy=getHeight()/(float)bmp.getHeight(),s=Math.min(sx,sy);int dw=Math.round(bmp.getWidth()*s),dh=Math.round(bmp.getHeight()*s),l=(getWidth()-dw)/2,t=(getHeight()-dh)/2;c.drawBitmap(bmp,null,new Rect(l,t,l+dw,t+dh),p);} else {c.drawText("M6A2 FIX2 · mGBA ARM64 Runtime",42,110,bootPaint);c.drawText("core/audio timing decoupled from display VSYNC",42,150,bootPaint);} }
    }
}
