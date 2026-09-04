#!/usr/bin/env python3
from pathlib import Path
import argparse

JAVA_MARKER='M6X1_R2_FINAL_SHOWDOWN_PRESENTATION_AUTHORITY'


def patch_java(path:Path):
    text=path.read_text()
    if JAVA_MARKER in text:return 'already'

    import_anchor='import android.graphics.Paint;\n'
    if import_anchor not in text:raise SystemExit('Java Paint import anchor missing')
    text=text.replace(import_anchor,import_anchor+'import android.graphics.PorterDuff;\nimport android.graphics.PorterDuffColorFilter;\n',1)

    native_anchor='    static native int nativeGetPlayerProxy(int[] out);\n'
    if native_anchor not in text:raise SystemExit('Java nativeGetPlayerProxy declaration missing')
    text=text.replace(native_anchor,native_anchor+'    static native int nativeGetPresentationState(int[] out);\n',1)

    report_anchor='j.put("showdown_compositor_in_apk",true);j.put("showdown_assets_in_apk",false);j.put("external_pack_required",true);'
    report_repl=(report_anchor+
        'j.put("presentation_semantics","M6X1_R2_M2R5D_M2R11E_M2R12G_M3S1_FINAL_PORT");'
        'j.put("provider_animation_clock","rom_frame");j.put("bridge_snapshot_policy","last_known_good_atomic_swap");'
        'j.put("hud_bounce_mon_decoupled",true);j.put("proxy_generation_changes",gameView.proxyGenerationChanges);'
        'j.put("proxy_release_events",gameView.proxyReleaseEvents);j.put("proxy_presentation_hidden_edges",gameView.proxyHiddenEdges);'
        'j.put("proxy_monbg_visible_frames",gameView.proxyMonBgVisibleFrames);j.put("stat_native_composite_frames",gameView.statOverlayFrames);'
        'j.put("bottom_ui_native_composite_frames",gameView.bottomUiRestoreFrames);')
    if report_anchor not in text:raise SystemExit('Java report anchor missing')
    text=text.replace(report_anchor,report_repl,1)

    fields_anchor='final Paint paint=new Paint();final Paint bootPaint=new Paint(Paint.ANTI_ALIAS_FLAG);final int[]pixels=new int[256*224];final int[]proxy=new int[10];final short[]sourceBuf=new short[4096];'
    fields_repl=('final Paint paint=new Paint();final Paint statPaint=new Paint();final Paint bootPaint=new Paint(Paint.ANTI_ALIAS_FLAG);'
                 'final int[]pixels=new int[256*224];final int[]proxy=new int[14];final int[]presentation=new int[7];final short[]sourceBuf=new short[4096];')
    if fields_anchor not in text:raise SystemExit('RuntimeView field anchor missing')
    text=text.replace(fields_anchor,fields_repl,1)

    bitmap_anchor='Bitmap bmp;AudioTrack audio;'
    bitmap_repl='Bitmap bmp,compositeBmp;AudioTrack audio;'
    if bitmap_anchor not in text:raise SystemExit('RuntimeView bitmap anchor missing')
    text=text.replace(bitmap_anchor,bitmap_repl,1)

    counter_anchor='sourceQueueOverHardEvents,overlayFrames,overlayFailures;volatile int sourceQueuePeak,activeSpecies;'
    counter_repl=('sourceQueueOverHardEvents,overlayFrames,overlayFailures,bottomUiRestoreFrames,statOverlayFrames,'
                  'proxyGenerationChanges,proxyReleaseEvents,proxyHiddenEdges,proxyMonBgVisibleFrames;volatile int sourceQueuePeak,activeSpecies;')
    if counter_anchor not in text:raise SystemExit('RuntimeView counter anchor missing')
    text=text.replace(counter_anchor,counter_repl,1)

    state_anchor='Thread coreWorker,audioWorker;int nativeOutputRate,audioTrackRate,audioBufferBytes,audioBufferFrames,sourceQueueTargetShorts,sourceQueueHardShorts;long lastSave;'
    state_repl=('Thread coreWorker,audioWorker;int nativeOutputRate,audioTrackRate,audioBufferBytes,audioBufferFrames,sourceQueueTargetShorts,sourceQueueHardShorts;long lastSave;'
                'boolean presentationHadProxy,presentationVisibleOnce,lastPresentationVisible;int presentationSpecies,presentationSpriteId;long presentationEpochRomFrame;')
    if state_anchor not in text:raise SystemExit('RuntimeView lifecycle field anchor missing')
    text=text.replace(state_anchor,state_repl,1)

    ctor_anchor='RuntimeView(){super(MainActivity.this);paint.setFilterBitmap(false);bootPaint.setColor(Color.rgb(120,230,170));'
    ctor_repl='RuntimeView(){super(MainActivity.this);paint.setFilterBitmap(false);statPaint.setFilterBitmap(false);bootPaint.setColor(Color.rgb(120,230,170));'
    if ctor_anchor not in text:raise SystemExit('RuntimeView ctor anchor missing')
    text=text.replace(ctor_anchor,ctor_repl,1)

    reset_anchor='sourceQueueOverHardEvents=overlayFrames=overlayFailures=0;sourceQueuePeak=activeSpecies=0;'
    reset_repl=('sourceQueueOverHardEvents=overlayFrames=overlayFailures=bottomUiRestoreFrames=statOverlayFrames='
                'proxyGenerationChanges=proxyReleaseEvents=proxyHiddenEdges=proxyMonBgVisibleFrames=0;sourceQueuePeak=activeSpecies=0;'
                'presentationHadProxy=presentationVisibleOnce=lastPresentationVisible=false;presentationSpecies=presentationSpriteId=0;presentationEpochRomFrame=0;')
    if reset_anchor not in text:raise SystemExit('RuntimeView reset anchor missing')
    text=text.replace(reset_anchor,reset_repl,1)

    old_draw='''        @Override protected void onDraw(Canvas c){super.onDraw(c);if(bmp==null){c.drawText("M6X1 · External Showdown Bridge",42,105,bootPaint);c.drawText("registry + 65536 Hz audio authority",42,145,bootPaint);return;}float sx=getWidth()/(float)bmp.getWidth(),sy=getHeight()/(float)bmp.getHeight(),s=Math.min(sx,sy);int dw=Math.round(bmp.getWidth()*s),dh=Math.round(bmp.getHeight()*s),l=(getWidth()-dw)/2,t=(getHeight()-dh)/2;c.drawBitmap(bmp,null,new Rect(l,t,l+dw,t+dh),paint);if(nativeGetPlayerProxy(proxy)==1){int species=proxy[0];Provider p=providers.get(species);if(p==null){overlayFailures++;activeSpecies=0;return;}Bitmap frame=p.frameAt(SystemClock.uptimeMillis());if(frame==null){overlayFailures++;activeSpecies=species;return;}float cx=l+(proxy[2]+proxy[4])*s,cy=t+(proxy[3]+proxy[5])*s;float fw=frame.getWidth()*p.scale*s,fh=frame.getHeight()*p.scale*s;RectF dst=new RectF(cx-fw/2f,cy-fh/2f,cx+fw/2f,cy+fh/2f);c.drawBitmap(frame,null,dst,paint);overlayFrames++;activeSpecies=species;}else activeSpecies=0;}
'''
    new_draw=r'''        // M6X1_R2_FINAL_SHOWDOWN_PRESENTATION_AUTHORITY
        // The compositor works at the native mGBA framebuffer resolution first,
        // then scales the finished frame exactly once. This avoids device-space
        // clip quantization and keeps body/stat/UI in one coordinate system.
        private boolean bottomBattleUiPresent(int w,int h){
            if(w<32||h<32)return false;int y0=(h*112)/160,light=0,total=0;
            for(int y=y0;y<h;y+=2)for(int x=0;x<w;x+=2){int col=pixels[y*w+x];int r=(col>>>16)&255,g=(col>>>8)&255,b=col&255;if(r>165&&g>165&&b>165)light++;total++;}
            return total>0&&light/(double)total>.16;
        }
        private void restoreBottomBattleUiNative(Canvas nc,int w,int h){
            if(!bottomBattleUiPresent(w,h))return;int y0=(h*112)/160;
            nc.drawBitmap(bmp,new Rect(0,y0,w,h),new Rect(0,y0,w,h),paint);bottomUiRestoreFrames++;
        }
        private void resetPresentationProxy(){
            presentationHadProxy=presentationVisibleOnce=lastPresentationVisible=false;
            presentationSpecies=presentationSpriteId=0;presentationEpochRomFrame=0;
        }
        private boolean updatePresentationProxy(){
            if(nativeGetPlayerProxy(proxy)!=1){
                if(presentationHadProxy)proxyReleaseEvents++;
                resetPresentationProxy();activeSpecies=0;return false;
            }
            int species=proxy[0],spriteId=proxy[13];long romFrame=Integer.toUnsignedLong(proxy[8]);
            boolean presentationVisible=proxy[10]!=0;
            if(!presentationHadProxy||species!=presentationSpecies||spriteId!=presentationSpriteId){
                if(presentationHadProxy)proxyReleaseEvents++;
                presentationHadProxy=true;presentationSpecies=species;presentationSpriteId=spriteId;
                presentationVisibleOnce=false;lastPresentationVisible=false;presentationEpochRomFrame=romFrame;proxyGenerationChanges++;
            }
            if(presentationVisible&&!presentationVisibleOnce){presentationVisibleOnce=true;presentationEpochRomFrame=romFrame;}
            if(presentationVisible!=lastPresentationVisible){if(!presentationVisible&&lastPresentationVisible)proxyHiddenEdges++;lastPresentationVisible=presentationVisible;}
            if(proxy[12]!=0&&presentationVisible)proxyMonBgVisibleFrames++;
            return presentationVisible&&presentationVisibleOnce;
        }
        private void drawStatOverlayNative(Canvas nc,Bitmap frame,RectF dst,int battler){
            if(nativeGetPresentationState(presentation)!=1||presentation[0]==0||presentation[1]!=battler||presentation[5]<=0)return;
            final int[][] colors={{255,96,80},{80,150,255},{255,220,80},{80,235,255},{210,100,255},{255,105,220},{90,235,165}};
            int pal=presentation[3],r=220,g=220,b=220;if(pal>=0&&pal<colors.length){r=colors[pal][0];g=colors[pal][1];b=colors[pal][2];}
            int alpha=Math.max(0,Math.min(210,presentation[5]*(presentation[4]!=0?16:14)));
            statPaint.setAlpha(alpha);statPaint.setColorFilter(new PorterDuffColorFilter(Color.rgb(r,g,b),PorterDuff.Mode.ADD));
            // Accepted M2R5D stat timing, but rasterized in native GBA space.
            // The entire composed frame is scaled afterward, so clip edges do not
            // become giant device-space blocks during the stat scroll.
            int stripe=Math.max(2,Math.round(dst.height()/10f)),gap=Math.max(3,stripe*2),phase=Math.floorMod(presentation[6],gap);
            for(int y=Math.round(dst.top)-gap+phase;y<dst.bottom;y+=gap){int save=nc.save();nc.clipRect(dst.left,y,dst.right,Math.min(dst.bottom,y+stripe));nc.drawBitmap(frame,null,dst,statPaint);nc.restoreToCount(save);}
            statPaint.setAlpha(255);statPaint.setColorFilter(null);statOverlayFrames++;
        }
        @Override protected void onDraw(Canvas c){
            super.onDraw(c);if(bmp==null){c.drawText("M6X1 · External Showdown Bridge",42,105,bootPaint);c.drawText("R2 final presentation authority",42,145,bootPaint);return;}
            int bw=bmp.getWidth(),bh=bmp.getHeight();
            if(compositeBmp==null||compositeBmp.getWidth()!=bw||compositeBmp.getHeight()!=bh)compositeBmp=Bitmap.createBitmap(bw,bh,Bitmap.Config.ARGB_8888);
            Canvas nc=new Canvas(compositeBmp);nc.drawBitmap(bmp,0,0,paint);
            if(updatePresentationProxy()){
                int species=proxy[0];Provider p=providers.get(species);
                if(p==null){overlayFailures++;activeSpecies=0;}
                else{
                    long romFrame=Integer.toUnsignedLong(proxy[8]);Bitmap frame=p.frameAtRomFrame(romFrame,presentationEpochRomFrame,nativeFps());
                    if(frame==null){overlayFailures++;activeSpecies=species;}
                    else{
                        float cx=proxy[2]+proxy[4],cy=proxy[3]+proxy[5],fw=frame.getWidth()*p.scale,fh=frame.getHeight()*p.scale;
                        RectF dst=new RectF(cx-fw/2f,cy-fh/2f,cx+fw/2f,cy+fh/2f);
                        nc.drawBitmap(frame,null,dst,paint);drawStatOverlayNative(nc,frame,dst,proxy[1]);overlayFrames++;activeSpecies=species;
                    }
                }
            }
            // M2R6C/M2R11E Z authority: lower battle UI is composited after the
            // external battler, in the SAME native coordinate space.
            restoreBottomBattleUiNative(nc,bw,bh);
            float sx=getWidth()/(float)bw,sy=getHeight()/(float)bh,s=Math.min(sx,sy);int dw=Math.round(bw*s),dh=Math.round(bh*s),l=(getWidth()-dw)/2,t=(getHeight()-dh)/2;
            c.drawBitmap(compositeBmp,null,new Rect(l,t,l+dw,t+dh),paint);
        }
'''
    if old_draw not in text:raise SystemExit('RuntimeView onDraw base block missing')
    text=text.replace(old_draw,new_draw,1)

    old_provider='''    static final class Provider{int species;String name;float scale=1;final ArrayList<AnimFrame>frames=new ArrayList<>();int cacheIndex=-1;Bitmap cache;long total(){long t=0;for(AnimFrame f:frames)t+=f.duration;return Math.max(1,t);}Bitmap frameAt(long now){if(frames.isEmpty())return null;long p=now%total(),a=0;int idx=0;for(int i=0;i<frames.size();i++){a+=frames.get(i).duration;if(p<a){idx=i;break;}}if(idx!=cacheIndex||cache==null||cache.isRecycled()){if(cache!=null&&!cache.isRecycled())cache.recycle();cache=BitmapFactory.decodeFile(frames.get(idx).file.getAbsolutePath());cacheIndex=idx;}return cache;}void recycle(){if(cache!=null&&!cache.isRecycled())cache.recycle();cache=null;cacheIndex=-1;}}
'''
    new_provider='''    static final class Provider{int species;String name;float scale=1;final ArrayList<AnimFrame>frames=new ArrayList<>();int cacheIndex=-1;Bitmap cache;long total(){long t=0;for(AnimFrame f:frames)t+=f.duration;return Math.max(1,t);}Bitmap frameAtRomFrame(long romFrame,long epoch,double fps){if(frames.isEmpty())return null;long df=Math.max(0,romFrame-epoch);long elapsed=(long)Math.floor(df*1000.0/Math.max(1.0,fps));long p=elapsed%total(),a=0;int idx=0;for(int i=0;i<frames.size();i++){a+=frames.get(i).duration;if(p<a){idx=i;break;}}if(idx!=cacheIndex||cache==null||cache.isRecycled()){if(cache!=null&&!cache.isRecycled())cache.recycle();cache=BitmapFactory.decodeFile(frames.get(idx).file.getAbsolutePath());cacheIndex=idx;}return cache;}void recycle(){if(cache!=null&&!cache.isRecycled())cache.recycle();cache=null;cacheIndex=-1;}}
'''
    if old_provider not in text:raise SystemExit('Provider wall-clock animation anchor missing')
    text=text.replace(old_provider,new_provider,1)

    # A successful R2 build must not retain the Android wall clock as provider animation authority.
    if 'frameAt(SystemClock.uptimeMillis())' in text:raise SystemExit('R2 wall-clock Showdown animation survivor')
    path.write_text(text);return 'patched'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args();root=Path(a.root)
    java=patch_java(root/'app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java')
    print('M6X1_ANDROID_PRESENTATION_R2_JAVA=PASS java='+java)

if __name__=='__main__':main()
