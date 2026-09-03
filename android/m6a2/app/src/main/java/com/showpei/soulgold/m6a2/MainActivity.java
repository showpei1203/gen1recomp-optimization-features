package com.showpei.soulgold.m6a2;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
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

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;

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
    private String romName="", romSha256="";
    private long romBytes;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        enterImmersive();

        File saves=new File(getFilesDir(),"saves"); saves.mkdirs();
        saveFile=new File(saves,"soulgold_runtime.sav");

        FrameLayout root=new FrameLayout(this);
        gameView=new RuntimeView();
        root.addView(gameView,new FrameLayout.LayoutParams(-1,-1));

        pickButton=new Button(this);
        pickButton.setText("選擇 SoulGold / GBA ROM");
        pickButton.setTextSize(18f);
        pickButton.setOnClickListener(v->chooseRom());
        FrameLayout.LayoutParams bp=new FrameLayout.LayoutParams(-2,-2);
        bp.leftMargin=42; bp.topMargin=170;
        root.addView(pickButton,bp);

        status=new TextView(this);
        status.setTextColor(Color.WHITE);
        status.setTextSize(15f);
        status.setBackgroundColor(0xAA101418);
        status.setPadding(16,10,16,10);
        FrameLayout.LayoutParams sp=new FrameLayout.LayoutParams(-2,-2);
        sp.leftMargin=18; sp.topMargin=18;
        root.addView(status,sp);
        setContentView(root);

        boolean ok=nativeInit(getApplicationInfo().nativeLibraryDir,getFilesDir().getAbsolutePath());
        if(!ok){
            status.setText("M6A2 FIX4A native/mGBA 初始化失敗："+nativeLastError());
            pickButton.setEnabled(false);
        } else {
            status.setText("SoulGold M6A2 FIX4A · Audio Clock Master\n"
                    +"mGBA 每幀音訊 → 明確重採樣 → Android 原生輸出時鐘。");
        }
    }

    @Override protected void onResume(){
        super.onResume();
        enterImmersive();
        gameView.resumeLoop();
    }

    @Override protected void onPause(){
        gameView.pauseLoop();
        saveNow();
        super.onPause();
    }

    @Override protected void onDestroy(){
        gameView.shutdownRuntime();
        nativeShutdown();
        super.onDestroy();
    }

    @Override public void onWindowFocusChanged(boolean focus){
        super.onWindowFocusChanged(focus);
        if(focus) enterImmersive();
    }

    private void enterImmersive(){
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY|
                View.SYSTEM_UI_FLAG_FULLSCREEN|
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION|
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    private void chooseRom(){
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("*/*");
        startActivityForResult(i,PICK_ROM);
    }

    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=PICK_ROM||result!=RESULT_OK||data==null||data.getData()==null)return;
        Uri uri=data.getData();
        try{
            String display=queryName(uri);
            if(display!=null&&!display.toLowerCase(Locale.ROOT).endsWith(".gba")){
                status.setText("拒絕：目前只接受 .gba。選到："+display);
                return;
            }

            File romDir=new File(getFilesDir(),"roms");
            romDir.mkdirs();
            File out=new File(romDir,"soulgold_user.gba");

            MessageDigest sha=MessageDigest.getInstance("SHA-256");
            long total=0;
            try(InputStream in=getContentResolver().openInputStream(uri);
                FileOutputStream fos=new FileOutputStream(out)){
                if(in==null)throw new Exception("無法開啟 ROM URI");
                byte[] buf=new byte[1<<16];
                int n;
                while((n=in.read(buf))>0){
                    fos.write(buf,0,n);
                    sha.update(buf,0,n);
                    total+=n;
                    if(total>128L*1024*1024)throw new Exception("ROM 過大");
                }
            }

            if(total<1024*1024)throw new Exception("檔案太小，不像 GBA ROM");
            romName=display==null?"soulgold_user.gba":display;
            romBytes=total;
            romSha256=hex(sha.digest());

            gameView.stopWorker();
            if(!nativeLoadRom(out.getAbsolutePath(),saveFile.getAbsolutePath()))
                throw new Exception(nativeLastError());

            gameView.startRuntime();
            pickButton.setVisibility(View.GONE);
            status.setVisibility(View.VISIBLE);
            status.setText(String.format(Locale.US,
                    "M6A2 FIX4A ACTIVE · core %.4f FPS · source %d Hz → device %d Hz\n"
                    +"Audio sink backpressure = emulation clock；VSYNC 只呈現畫面。",
                    nativeFps(),nativeSampleRate(),gameView.nativeOutputRate));
            status.postDelayed(()->status.setVisibility(View.GONE),7000);
        }catch(Exception ex){
            status.setVisibility(View.VISIBLE);
            status.setText("ROM boot 失敗："+ex.getMessage());
        }
    }

    private String queryName(Uri uri){
        try(Cursor c=getContentResolver().query(uri,null,null,null,null)){
            if(c!=null&&c.moveToFirst()){
                int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if(i>=0)return c.getString(i);
            }
        }catch(Exception ignored){}
        return null;
    }

    private static String hex(byte[] b){
        StringBuilder s=new StringBuilder();
        for(byte x:b)s.append(String.format(Locale.US,"%02x",x&255));
        return s.toString();
    }

    private boolean gameDevice(InputDevice d){
        if(d==null)return false;
        int s=d.getSources();
        return(s&InputDevice.SOURCE_GAMEPAD)==InputDevice.SOURCE_GAMEPAD||
              (s&InputDevice.SOURCE_JOYSTICK)==InputDevice.SOURCE_JOYSTICK;
    }

    private int retroId(int code){
        switch(code){
            case KeyEvent.KEYCODE_BUTTON_A:return RID_A;
            case KeyEvent.KEYCODE_BUTTON_B:return RID_B;
            case KeyEvent.KEYCODE_BUTTON_L1:return RID_L;
            case KeyEvent.KEYCODE_BUTTON_R1:return RID_R;
            case KeyEvent.KEYCODE_BUTTON_START:return RID_START;
            case KeyEvent.KEYCODE_BUTTON_SELECT:
            case KeyEvent.KEYCODE_BACK:return RID_SELECT;
            case KeyEvent.KEYCODE_DPAD_UP:return RID_UP;
            case KeyEvent.KEYCODE_DPAD_DOWN:return RID_DOWN;
            case KeyEvent.KEYCODE_DPAD_LEFT:return RID_LEFT;
            case KeyEvent.KEYCODE_DPAD_RIGHT:return RID_RIGHT;
            default:return-1;
        }
    }

    @Override public boolean dispatchKeyEvent(KeyEvent e){
        if(gameDevice(e.getDevice())){
            int id=retroId(e.getKeyCode());
            if(id>=0){
                if(e.getAction()==KeyEvent.ACTION_DOWN)inputMask|=1<<id;
                else if(e.getAction()==KeyEvent.ACTION_UP)inputMask&=~(1<<id);
                nativeSetInputMask(inputMask);

                if((inputMask&(1<<RID_L))!=0 &&
                   (inputMask&(1<<RID_R))!=0 &&
                   (inputMask&(1<<RID_START))!=0){
                    gameView.requestReset();
                }

                if((inputMask&(1<<RID_START))!=0 &&
                   (inputMask&(1<<RID_SELECT))!=0){
                    writeReport("start_select");
                }
                return true;
            }
        }
        return super.dispatchKeyEvent(e);
    }

    @Override public boolean dispatchGenericMotionEvent(MotionEvent e){
        if(gameDevice(e.getDevice())&&e.getAction()==MotionEvent.ACTION_MOVE){
            float x=e.getAxisValue(MotionEvent.AXIS_X);
            float y=e.getAxisValue(MotionEvent.AXIS_Y);
            int m=inputMask;
            m&=~((1<<RID_LEFT)|(1<<RID_RIGHT)|(1<<RID_UP)|(1<<RID_DOWN));
            if(x<-0.5f)m|=1<<RID_LEFT;
            else if(x>0.5f)m|=1<<RID_RIGHT;
            if(y<-0.5f)m|=1<<RID_UP;
            else if(y>0.5f)m|=1<<RID_DOWN;
            inputMask=m;
            nativeSetInputMask(m);
            return true;
        }
        return super.dispatchGenericMotionEvent(e);
    }

    private void saveNow(){
        if(gameView.loaded)nativeSaveSram(saveFile.getAbsolutePath());
    }

    private void writeReport(String reason){
        try{
            JSONObject j=new JSONObject();
            j.put("milestone","M6A2_FIX4A");
            j.put("reason",reason);
            j.put("manufacturer",Build.MANUFACTURER);
            j.put("model",Build.MODEL);
            j.put("sdk",Build.VERSION.SDK_INT);

            JSONArray a=new JSONArray();
            for(String abi:Build.SUPPORTED_ABIS)a.put(abi);
            j.put("abis",a);
            j.put("rom_name",romName);
            j.put("rom_bytes",romBytes);
            j.put("rom_sha256",romSha256);

            long frames=gameView.frames;
            long gen=nativeAudioGeneratedSamples();
            double fps=nativeFps();
            double effective=(frames>0)?(gen/2.0)*fps/frames:0.0;

            long playbackHead=gameView.playbackHeadFrames();
            long writtenFrames=gameView.audioWrittenSamples/2L;
            long queuedFrames=Math.max(0L,writtenFrames-playbackHead);
            double queuedMs=gameView.audioTrackRate>0
                    ?1000.0*queuedFrames/gameView.audioTrackRate:0.0;

            j.put("core_reported_fps",fps);
            j.put("source_reported_rate",nativeSampleRate());
            j.put("effective_generated_source_rate",effective);
            j.put("native_output_rate",gameView.nativeOutputRate);
            j.put("audio_track_rate",gameView.audioTrackRate);
            j.put("audio_track_buffer_bytes",gameView.audioBufferBytes);
            j.put("audio_track_buffer_frames",gameView.audioBufferFrames);

            j.put("emu_frames",frames);
            j.put("display_callbacks",gameView.displayCallbacks);
            j.put("audio_generated_source_samples",gen);
            j.put("audio_drained_source_samples",nativeAudioDrainedSamples());
            j.put("audio_dropped_source_samples",nativeAudioDroppedSamples());
            j.put("discarded_source_samples",gameView.discardedSourceSamples);
            j.put("audio_written_output_samples",gameView.audioWrittenSamples);
            j.put("audio_write_errors",gameView.audioWriteErrors);
            j.put("playback_head_output_frames",playbackHead);
            j.put("estimated_sink_queued_frames",queuedFrames);
            j.put("estimated_sink_latency_ms",queuedMs);
            j.put("native_audio_queue_samples",nativeAudioQueueSamples());
            j.put("audio_underrun_count",gameView.underrunCount());

            AudioTimestamp ts=gameView.audioTimestamp();
            if(ts!=null){
                j.put("audio_timestamp_frame_position",ts.framePosition);
                j.put("audio_timestamp_nano_time",ts.nanoTime);
            }

            j.put("audio_clock_master",true);
            j.put("explicit_frontend_resampler","linear_continuous_phase");
            j.put("choreographer_advances_emulation",false);
            j.put("large_java_pending_queue",false);
            j.put("async_native_audio_queue_growth",false);
            j.put("fix2_audio_worker_rejected",true);
            j.put("fix3_choreographer_master_rejected",true);
            j.put("showdown_overlay_in_apk",false);

            j.put("rules",new JSONArray()
                    .put("R-SD-155").put("R-SD-156").put("R-SD-157")
                    .put("R-SD-158").put("R-SD-159").put("R-SD-160")
                    .put("R-SD-161").put("R-SD-162"));

            File base=getExternalFilesDir(null);
            if(base==null)base=getFilesDir();
            File out=new File(base,"M6A2_FIX4A_AUDIO_CLOCK_REPORT.json");
            try(FileOutputStream f=new FileOutputStream(out)){
                f.write(j.toString(2).getBytes(StandardCharsets.UTF_8));
            }
        }catch(Exception ignored){}
    }

    final class RuntimeView extends View implements Choreographer.FrameCallback {
        final Paint p=new Paint();
        final Paint bootPaint=new Paint(Paint.ANTI_ALIAS_FLAG);
        final int[] pixels=new int[256*224];
        final short[] sourceBuf=new short[4096];
        final short[] outputBuf=new short[8192];
        final LinearResampler resampler=new LinearResampler();

        Bitmap bmp;
        AudioTrack audio;
        volatile boolean loop;
        volatile boolean loaded;
        volatile boolean workerRun;
        volatile boolean resetRequested;
        volatile long frames;
        volatile long displayCallbacks;
        volatile long audioWrittenSamples;
        volatile long audioWriteErrors;
        volatile long discardedSourceSamples;

        Thread worker;
        int nativeOutputRate;
        int audioTrackRate;
        int audioBufferBytes;
        int audioBufferFrames;
        int prefillOutputShorts;
        long audioSessionWrittenSamples;
        long lastSave;

        RuntimeView(){
            super(MainActivity.this);
            p.setFilterBitmap(false);
            bootPaint.setColor(Color.rgb(120,230,170));
            bootPaint.setTextSize(30f);
            setBackgroundColor(Color.BLACK);
        }

        void resumeLoop(){
            if(!loop){
                loop=true;
                Choreographer.getInstance().postFrameCallback(this);
            }
            if(loaded)startWorker();
        }

        void pauseLoop(){
            loop=false;
            stopWorker();
            discardNativeAudio();
        }

        void startRuntime(){
            loaded=true;
            frames=0;
            displayCallbacks=0;
            audioWrittenSamples=0;
            audioWriteErrors=0;
            discardedSourceSamples=0;
            resetRequested=false;
            lastSave=SystemClock.elapsedRealtime();
            discardNativeAudio();
            initAudio();
            resampler.reset(nativeSampleRate(),nativeOutputRate);
            startWorker();
            resumeLoop();
            invalidate();
        }

        void shutdownRuntime(){
            loop=false;
            stopWorker();
            discardNativeAudio();
            closeAudio();
            loaded=false;
        }

        void requestReset(){
            if(loaded)resetRequested=true;
        }

        void initAudio(){
            closeAudio();

            int src=nativeSampleRate();
            if(src<8000)src=32768;

            nativeOutputRate=AudioTrack.getNativeOutputSampleRate(AudioManager.STREAM_MUSIC);
            if(nativeOutputRate<8000)nativeOutputRate=48000;

            int min=AudioTrack.getMinBufferSize(
                    nativeOutputRate,
                    AudioFormat.CHANNEL_OUT_STEREO,
                    AudioFormat.ENCODING_PCM_16BIT);
            if(min<0)min=4096;

            double fps=Math.max(1.0,nativeFps());
            int oneFrameShorts=(int)Math.ceil(nativeOutputRate/fps)*2;
            prefillOutputShorts=Math.max(256,oneFrameShorts);
            audioBufferBytes=Math.max(min,prefillOutputShorts*2);

            AudioAttributes attrs=new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_GAME)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build();

            AudioFormat fmt=new AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setSampleRate(nativeOutputRate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                    .build();

            AudioTrack.Builder b=new AudioTrack.Builder()
                    .setAudioAttributes(attrs)
                    .setAudioFormat(fmt)
                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .setBufferSizeInBytes(audioBufferBytes);

            if(Build.VERSION.SDK_INT>=26){
                b.setPerformanceMode(AudioTrack.PERFORMANCE_MODE_LOW_LATENCY);
            }

            audio=b.build();
            audioTrackRate=audio.getSampleRate();
            audioBufferFrames=audio.getBufferSizeInFrames();
            audioSessionWrittenSamples=0;
        }

        void closeAudio(){
            if(audio!=null){
                try{
                    audio.pause();
                    audio.flush();
                    audio.release();
                }catch(Exception ignored){}
                audio=null;
            }
        }

        void startWorker(){
            if(!loaded||workerRun||audio==null)return;
            discardNativeAudio();
            resampler.reset(nativeSampleRate(),audioTrackRate);
            audioSessionWrittenSamples=0;
            workerRun=true;
            worker=new Thread(this::audioClockLoop,"SoulGold-M6A2-AudioClock");
            worker.start();
        }

        void stopWorker(){
            workerRun=false;
            if(audio!=null){
                try{
                    audio.pause();
                    audio.flush();
                }catch(Exception ignored){}
            }
            Thread w=worker;
            worker=null;
            if(w!=null&&w!=Thread.currentThread()){
                try{w.join(1500);}catch(InterruptedException ignored){
                    Thread.currentThread().interrupt();
                }
            }
            audioSessionWrittenSamples=0;
        }

        void audioClockLoop(){
            Process.setThreadPriority(Process.THREAD_PRIORITY_AUDIO);
            boolean playing=false;

            while(workerRun&&loaded){
                if(resetRequested){
                    resetRequested=false;
                    try{
                        if(audio!=null){
                            audio.pause();
                            audio.flush();
                        }
                    }catch(Exception ignored){}
                    playing=false;
                    audioSessionWrittenSamples=0;
                    discardNativeAudio();
                    resampler.reset(nativeSampleRate(),audioTrackRate);
                    nativeReset();
                }

                nativeRunFrame();
                frames++;

                int produced=drainAndWrite();
                if(produced<0)break;

                if(!playing &&
                   audio!=null &&
                   audioSessionWrittenSamples>=prefillOutputShorts){
                    try{
                        audio.play();
                        playing=true;
                    }catch(Exception ex){
                        audioWriteErrors++;
                        break;
                    }
                }

                long now=SystemClock.elapsedRealtime();
                if(now-lastSave>5000){
                    nativeSaveSram(saveFile.getAbsolutePath());
                    lastSave=now;
                }
            }
        }

        int drainAndWrite(){
            int totalOutput=0;
            while(workerRun){
                int n=nativeDrainAudio(sourceBuf);
                if(n<=0)break;
                int out=resampler.process(sourceBuf,n,outputBuf);
                if(out<=0)continue;

                int off=0;
                while(workerRun&&off<out){
                    int w;
                    try{
                        w=audio.write(outputBuf,off,out-off,AudioTrack.WRITE_BLOCKING);
                    }catch(Exception ex){
                        audioWriteErrors++;
                        return -1;
                    }
                    if(w>0){
                        off+=w;
                        audioWrittenSamples+=w;
                        audioSessionWrittenSamples+=w;
                        totalOutput+=w;
                    }else{
                        audioWriteErrors++;
                        return -1;
                    }
                }
            }
            return totalOutput;
        }

        void discardNativeAudio(){
            int n;
            do{
                n=nativeDrainAudio(sourceBuf);
                if(n>0)discardedSourceSamples+=n;
            }while(n>0);
        }

        void copyLatestFrame(){
            int info=nativeCopyFrame(pixels);
            if(info<=0)return;
            int w=(info>>>16)&0xffff;
            int h=info&0xffff;
            if(w<=0||h<=0)return;
            if(bmp==null||bmp.getWidth()!=w||bmp.getHeight()!=h)
                bmp=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
            bmp.setPixels(pixels,0,w,0,0,w,h);
        }

        long playbackHeadFrames(){
            AudioTrack a=audio;
            if(a==null)return 0;
            return Integer.toUnsignedLong(a.getPlaybackHeadPosition());
        }

        int underrunCount(){
            AudioTrack a=audio;
            return a==null?0:a.getUnderrunCount();
        }

        AudioTimestamp audioTimestamp(){
            AudioTrack a=audio;
            if(a==null)return null;
            AudioTimestamp ts=new AudioTimestamp();
            try{
                return a.getTimestamp(ts)?ts:null;
            }catch(Exception ignored){
                return null;
            }
        }

        @Override public void doFrame(long ns){
            if(!loop)return;
            displayCallbacks++;
            if(loaded)copyLatestFrame();
            invalidate();
            Choreographer.getInstance().postFrameCallback(this);
        }

        @Override protected void onDraw(Canvas c){
            super.onDraw(c);
            if(bmp!=null){
                float sx=getWidth()/(float)bmp.getWidth();
                float sy=getHeight()/(float)bmp.getHeight();
                float s=Math.min(sx,sy);
                int dw=Math.round(bmp.getWidth()*s);
                int dh=Math.round(bmp.getHeight()*s);
                int l=(getWidth()-dw)/2;
                int t=(getHeight()-dh)/2;
                c.drawBitmap(bmp,null,new Rect(l,t,l+dw,t+dh),p);
            }else{
                c.drawText("M6A2 FIX4A · mGBA ARM64 Runtime",42,110,bootPaint);
                c.drawText("audio-clock master / explicit resampler",42,150,bootPaint);
            }
        }
    }

    static final class LinearResampler {
        private int srcRate=32768;
        private int dstRate=48000;
        private double step=32768.0/48000.0;
        private double pos=0.0;
        private short prevL,prevR;
        private boolean havePrev;

        void reset(int src,int dst){
            srcRate=src>0?src:32768;
            dstRate=dst>0?dst:48000;
            step=srcRate/(double)dstRate;
            pos=0.0;
            havePrev=false;
            prevL=prevR=0;
        }

        int process(short[] in,int shorts,short[] out){
            int frames=shorts/2;
            if(frames<=0)return 0;

            if(!havePrev){
                prevL=in[0];
                prevR=in[1];
                havePrev=true;
            }

            int o=0;
            while(pos<frames && o+1<out.length){
                int base=(int)Math.floor(pos);
                double frac=pos-base;

                short l0,r0,l1,r1;
                if(base==0){
                    l0=prevL;
                    r0=prevR;
                }else{
                    int p=(base-1)*2;
                    l0=in[p];
                    r0=in[p+1];
                }

                int next=base*2;
                if(next+1<shorts){
                    l1=in[next];
                    r1=in[next+1];
                }else{
                    l1=in[shorts-2];
                    r1=in[shorts-1];
                }

                int l=(int)Math.round(l0+(l1-l0)*frac);
                int r=(int)Math.round(r0+(r1-r0)*frac);
                out[o++]=(short)Math.max(Short.MIN_VALUE,Math.min(Short.MAX_VALUE,l));
                out[o++]=(short)Math.max(Short.MIN_VALUE,Math.min(Short.MAX_VALUE,r));
                pos+=step;
            }

            pos-=frames;
            prevL=in[shorts-2];
            prevR=in[shorts-1];
            return o;
        }
    }
}
