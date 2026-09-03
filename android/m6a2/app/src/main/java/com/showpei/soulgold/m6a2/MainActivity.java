package com.showpei.soulgold.m6a2;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
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
        FrameLayout.LayoutParams bp=new FrameLayout.LayoutParams(-2,-2); bp.leftMargin=42; bp.topMargin=170;
        root.addView(pickButton,bp);

        status=new TextView(this);
        status.setTextColor(Color.WHITE); status.setTextSize(15f); status.setBackgroundColor(0xAA101418); status.setPadding(16,10,16,10);
        FrameLayout.LayoutParams sp=new FrameLayout.LayoutParams(-2,-2); sp.leftMargin=18; sp.topMargin=18;
        root.addView(status,sp); setContentView(root);

        boolean ok=nativeInit(getApplicationInfo().nativeLibraryDir,getFilesDir().getAbsolutePath());
        if(!ok){ status.setText("M6A2 FIX3 native/mGBA 初始化失敗："+nativeLastError()); pickButton.setEnabled(false); }
        else status.setText("SoulGold M6A2 FIX3 · Conservative Audio/Pacing\nFIX2 audio worker 已回滾。請選擇你自己的 .gba 備份。");
    }

    @Override protected void onResume(){ super.onResume(); enterImmersive(); gameView.resumeLoop(); }
    @Override protected void onPause(){ gameView.pauseLoop(); saveNow(); super.onPause(); }
    @Override protected void onDestroy(){ gameView.closeAudio(); nativeShutdown(); super.onDestroy(); }
    @Override public void onWindowFocusChanged(boolean focus){ super.onWindowFocusChanged(focus); if(focus) enterImmersive(); }

    private void enterImmersive(){ getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY|View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_LAYOUT_STABLE); }

    private void chooseRom(){ Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT); i.addCategory(Intent.CATEGORY_OPENABLE); i.setType("*/*"); startActivityForResult(i,PICK_ROM); }

    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=PICK_ROM||result!=RESULT_OK||data==null||data.getData()==null)return;
        Uri uri=data.getData();
        try{
            String display=queryName(uri);
            if(display!=null&&!display.toLowerCase(Locale.ROOT).endsWith(".gba")){ status.setText("拒絕：目前只接受 .gba。選到："+display); return; }
            File romDir=new File(getFilesDir(),"roms"); romDir.mkdirs(); File out=new File(romDir,"soulgold_user.gba");
            MessageDigest sha=MessageDigest.getInstance("SHA-256"); long total=0;
            try(InputStream in=getContentResolver().openInputStream(uri); FileOutputStream fos=new FileOutputStream(out)){
                if(in==null)throw new Exception("無法開啟 ROM URI"); byte[] buf=new byte[1<<16]; int n;
                while((n=in.read(buf))>0){fos.write(buf,0,n);sha.update(buf,0,n);total+=n;if(total>128L*1024*1024)throw new Exception("ROM 過大");}
            }
            if(total<1024*1024)throw new Exception("檔案太小，不像 GBA ROM");
            romName=display==null?"soulgold_user.gba":display; romBytes=total; romSha256=hex(sha.digest());
            if(!nativeLoadRom(out.getAbsolutePath(),saveFile.getAbsolutePath()))throw new Exception(nativeLastError());
            gameView.startRuntime(); pickButton.setVisibility(View.GONE);
            status.setText(String.format(Locale.US,"M6A2 FIX3 ACTIVE · core %.4f FPS · source audio %d Hz\nVSYNC timestamp accumulator + retained partial audio writes。",nativeFps(),nativeSampleRate()));
            status.postDelayed(()->status.setVisibility(View.GONE),7000);
        }catch(Exception ex){status.setVisibility(View.VISIBLE);status.setText("ROM boot 失敗："+ex.getMessage());}
    }

    private String queryName(Uri uri){ try(Cursor c=getContentResolver().query(uri,null,null,null,null)){if(c!=null&&c.moveToFirst()){int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);if(i>=0)return c.getString(i);}}catch(Exception ignored){}return null; }
    private static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format(Locale.US,"%02x",x&255));return s.toString();}

    private boolean gameDevice(InputDevice d){if(d==null)return false;int s=d.getSources();return(s&InputDevice.SOURCE_GAMEPAD)==InputDevice.SOURCE_GAMEPAD||(s&InputDevice.SOURCE_JOYSTICK)==InputDevice.SOURCE_JOYSTICK;}
    private int retroId(int code){switch(code){case KeyEvent.KEYCODE_BUTTON_A:return RID_A;case KeyEvent.KEYCODE_BUTTON_B:return RID_B;case KeyEvent.KEYCODE_BUTTON_L1:return RID_L;case KeyEvent.KEYCODE_BUTTON_R1:return RID_R;case KeyEvent.KEYCODE_BUTTON_START:return RID_START;case KeyEvent.KEYCODE_BUTTON_SELECT:case KeyEvent.KEYCODE_BACK:return RID_SELECT;case KeyEvent.KEYCODE_DPAD_UP:return RID_UP;case KeyEvent.KEYCODE_DPAD_DOWN:return RID_DOWN;case KeyEvent.KEYCODE_DPAD_LEFT:return RID_LEFT;case KeyEvent.KEYCODE_DPAD_RIGHT:return RID_RIGHT;default:return-1;}}
    @Override public boolean dispatchKeyEvent(KeyEvent e){if(gameDevice(e.getDevice())){int id=retroId(e.getKeyCode());if(id>=0){if(e.getAction()==KeyEvent.ACTION_DOWN)inputMask|=1<<id;else if(e.getAction()==KeyEvent.ACTION_UP)inputMask&=~(1<<id);nativeSetInputMask(inputMask);if((inputMask&(1<<RID_L))!=0&&(inputMask&(1<<RID_R))!=0&&(inputMask&(1<<RID_START))!=0)nativeReset();if((inputMask&(1<<RID_START))!=0&&(inputMask&(1<<RID_SELECT))!=0)writeReport("start_select");return true;}}return super.dispatchKeyEvent(e);}
    @Override public boolean dispatchGenericMotionEvent(MotionEvent e){if(gameDevice(e.getDevice())&&e.getAction()==MotionEvent.ACTION_MOVE){float x=e.getAxisValue(MotionEvent.AXIS_X),y=e.getAxisValue(MotionEvent.AXIS_Y);int m=inputMask;m&=~((1<<RID_LEFT)|(1<<RID_RIGHT)|(1<<RID_UP)|(1<<RID_DOWN));if(x<-0.5f)m|=1<<RID_LEFT;else if(x>0.5f)m|=1<<RID_RIGHT;if(y<-0.5f)m|=1<<RID_UP;else if(y>0.5f)m|=1<<RID_DOWN;inputMask=m;nativeSetInputMask(m);return true;}return super.dispatchGenericMotionEvent(e);}

    private void saveNow(){if(gameView.loaded)nativeSaveSram(saveFile.getAbsolutePath());}
    private void writeReport(String reason){
        try{
            JSONObject j=new JSONObject(); j.put("milestone","M6A2_FIX3"); j.put("reason",reason); j.put("manufacturer",Build.MANUFACTURER); j.put("model",Build.MODEL); j.put("sdk",Build.VERSION.SDK_INT);
            JSONArray a=new JSONArray();for(String abi:Build.SUPPORTED_ABIS)a.put(abi);j.put("abis",a);j.put("rom_name",romName);j.put("rom_bytes",romBytes);j.put("rom_sha256",romSha256);
            long frames=gameView.frames,gen=nativeAudioGeneratedSamples(); double fps=nativeFps(); double effective=(frames>0)?(gen/2.0)*fps/frames:0.0;
            j.put("core_reported_fps",fps);j.put("source_reported_rate",nativeSampleRate());j.put("effective_generated_source_rate",effective);j.put("native_output_rate",gameView.nativeOutputRate);j.put("audio_track_rate",gameView.audioTrackRate);
            j.put("emu_frames",frames);j.put("display_callbacks",gameView.displayCallbacks);j.put("audio_generated_samples",gen);j.put("audio_drained_samples",nativeAudioDrainedSamples());j.put("audio_dropped_samples",nativeAudioDroppedSamples());j.put("audio_written_samples",gameView.audioWrittenSamples);j.put("audio_partial_writes",gameView.audioPartialWrites);j.put("audio_zero_writes",gameView.audioZeroWrites);j.put("host_pending_samples",gameView.pendingSize);j.put("host_pending_peak",gameView.pendingPeak);j.put("native_audio_queue_samples",nativeAudioQueueSamples());
            j.put("fix2_audio_worker_rejected",true);j.put("choreographer_timestamp_accumulator",true);j.put("menu_presentation_changed_by_fix3",false);j.put("showdown_overlay_in_apk",false);
            j.put("rules",new JSONArray().put("R-SD-149").put("R-SD-150").put("R-SD-151").put("R-SD-152").put("R-SD-153").put("R-SD-154"));
            File base=getExternalFilesDir(null);if(base==null)base=getFilesDir();File out=new File(base,"M6A2_FIX3_AUDIO_PACING_REPORT.json");try(FileOutputStream f=new FileOutputStream(out)){f.write(j.toString(2).getBytes(StandardCharsets.UTF_8));}
        }catch(Exception ignored){}
    }

    final class RuntimeView extends View implements Choreographer.FrameCallback {
        final Paint p=new Paint();final Paint bootPaint=new Paint(Paint.ANTI_ALIAS_FLAG);final int[] pixels=new int[256*224];final short[] drainBuf=new short[8192];final short[] pending=new short[65536];Bitmap bmp;
        AudioTrack audio;boolean loop,loaded,audioStarted;long frames,displayCallbacks,lastSave,lastVsyncNs,lastFpsNs;int fpsFrames;float renderFps;double frameBudget;double coreFps;
        int pendingHead,pendingSize,pendingPeak,prefillShorts,nativeOutputRate,audioTrackRate;long audioWrittenSamples,audioPartialWrites,audioZeroWrites;

        RuntimeView(){super(MainActivity.this);p.setFilterBitmap(false);bootPaint.setColor(Color.rgb(120,230,170));bootPaint.setTextSize(30f);setBackgroundColor(Color.BLACK);}
        void resumeLoop(){if(!loop){loop=true;lastVsyncNs=0;frameBudget=Math.max(frameBudget,1.0);Choreographer.getInstance().postFrameCallback(this);}}
        void pauseLoop(){loop=false;lastVsyncNs=0;if(audio!=null){try{audio.pause();audio.flush();}catch(Exception ignored){}}audioStarted=false;pendingHead=0;pendingSize=0;}
        void startRuntime(){loaded=true;frames=0;displayCallbacks=0;frameBudget=1.0;coreFps=Math.max(1.0,nativeFps());lastSave=SystemClock.elapsedRealtime();audioWrittenSamples=audioPartialWrites=audioZeroWrites=0;pendingHead=pendingSize=pendingPeak=0;initAudio();resumeLoop();invalidate();}
        void initAudio(){closeAudio();int sr=nativeSampleRate();if(sr<8000)sr=32768;nativeOutputRate=AudioTrack.getNativeOutputSampleRate(AudioManager.STREAM_MUSIC);int min=AudioTrack.getMinBufferSize(sr,AudioFormat.CHANNEL_OUT_STEREO,AudioFormat.ENCODING_PCM_16BIT);if(min<0)min=8192;int bytes=Math.max(min*2,16384);audio=new AudioTrack(AudioManager.STREAM_MUSIC,sr,AudioFormat.CHANNEL_OUT_STEREO,AudioFormat.ENCODING_PCM_16BIT,bytes,AudioTrack.MODE_STREAM);audioTrackRate=audio.getSampleRate();prefillShorts=Math.max(4096,Math.min(8192,bytes/2));audioStarted=false;}
        void closeAudio(){if(audio!=null){try{audio.pause();audio.flush();audio.release();}catch(Exception ignored){}audio=null;}audioStarted=false;}
        void appendPending(short[] src,int n){int tail=(pendingHead+pendingSize)%pending.length;int first=Math.min(n,pending.length-tail);System.arraycopy(src,0,pending,tail,first);if(n>first)System.arraycopy(src,first,pending,0,n-first);pendingSize+=n;if(pendingSize>pendingPeak)pendingPeak=pendingSize;}
        void drainNative(){while(pending.length-pendingSize>=drainBuf.length){int n=nativeDrainAudio(drainBuf);if(n<=0)break;appendPending(drainBuf,n);}}
        int writePendingOnce(){if(audio==null||pendingSize<=0)return 0;int contiguous=Math.min(pendingSize,pending.length-pendingHead);int request=Math.min(contiguous,8192);int w=audio.write(pending,pendingHead,request,AudioTrack.WRITE_NON_BLOCKING);if(w>0){if(w<request)audioPartialWrites++;pendingHead=(pendingHead+w)%pending.length;pendingSize-=w;audioWrittenSamples+=w;}else if(w==0)audioZeroWrites++;return w;}
        void pumpAudio(){if(audio==null)return;if(!audioStarted){if(pendingSize<prefillShorts)return;int primed=0;for(int i=0;i<4&&pendingSize>0&&primed<prefillShorts;i++){int w=writePendingOnce();if(w<=0)break;primed+=w;}if(primed>0){try{audio.play();audioStarted=true;}catch(Exception ignored){}}return;}for(int i=0;i<4&&pendingSize>0;i++){if(writePendingOnce()<=0)break;}}
        void copyLatestFrame(){int info=nativeCopyFrame(pixels);if(info<=0)return;int w=(info>>>16)&0xffff,h=info&0xffff;if(w<=0||h<=0)return;if(bmp==null||bmp.getWidth()!=w||bmp.getHeight()!=h)bmp=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);bmp.setPixels(pixels,0,w,0,0,w,h);}

        @Override public void doFrame(long ns){
            if(!loop)return;displayCallbacks++;
            if(lastFpsNs==0)lastFpsNs=ns;fpsFrames++;if(ns-lastFpsNs>=1_000_000_000L){renderFps=(float)(fpsFrames*1e9/(ns-lastFpsNs));fpsFrames=0;lastFpsNs=ns;}
            if(lastVsyncNs==0)lastVsyncNs=ns;long dt=ns-lastVsyncNs;lastVsyncNs=ns;if(dt<0||dt>100_000_000L)dt=0;
            if(loaded){frameBudget+=dt*coreFps/1_000_000_000.0;int runs=(int)frameBudget;if(runs>4)runs=4;frameBudget-=runs;for(int i=0;i<runs;i++){nativeRunFrame();frames++;}if(runs>0){copyLatestFrame();drainNative();}pumpAudio();long now=SystemClock.elapsedRealtime();if(now-lastSave>5000){nativeSaveSram(saveFile.getAbsolutePath());lastSave=now;}invalidate();}
            Choreographer.getInstance().postFrameCallback(this);
        }
        @Override protected void onDraw(Canvas c){super.onDraw(c);if(bmp!=null){float sx=getWidth()/(float)bmp.getWidth(),sy=getHeight()/(float)bmp.getHeight(),s=Math.min(sx,sy);int dw=Math.round(bmp.getWidth()*s),dh=Math.round(bmp.getHeight()*s),l=(getWidth()-dw)/2,t=(getHeight()-dh)/2;c.drawBitmap(bmp,null,new Rect(l,t,l+dw,t+dh),p);}else{c.drawText("M6A2 FIX3 · mGBA ARM64 Runtime",42,110,bootPaint);c.drawText("conservative audio/pacing rollback",42,150,bootPaint);}}
    }
}
