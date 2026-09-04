#!/usr/bin/env python3
from pathlib import Path
import argparse

JAVA_MARKER='M6X1_R1_M2R11E_PRESENTATION_PORT'
CPP_MARKER='M6X1_R1_STAT_EWRAM_READER'


def patch_cpp(path:Path):
    text=path.read_text()
    if CPP_MARKER in text:
        return 'already'
    anchor='''extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPlayerProxy(JNIEnv*e,jclass,jintArray out){
  if(!gBridgeFresh.load(std::memory_order_relaxed)||!out||e->GetArrayLength(out)<10)return 0;Bridge b{};{std::lock_guard<std::mutex>lk(gBridgeMu);b=gCachedBridge;}
  for(const Proxy&p:b.proxy){if(p.valid&&p.side==0&&p.visible&&isBackProvider(p.species)){jint v[10]={(jint)p.species,(jint)p.battler,(jint)p.x,(jint)p.y,(jint)p.x2,(jint)p.y2,(jint)p.hFlip,(jint)p.vFlip,(jint)b.romFrame,(jint)p.side};e->SetIntArrayRegion(out,0,10,v);return 1;}}
  return 0;
}
'''
    if anchor not in text:
        raise SystemExit('nativeGetPlayerProxy anchor missing')
    addition=r'''

// M6X1_R1_STAT_EWRAM_READER
// M2R11E presentation authority is transported from ROM-owned EWRAM globals.
// The bridge registry ABI remains v1; these are read-only presentation taps.
template<typename T> static bool m6x1ReadEwramAbs(uint32_t addr,T*out){
  if(!out||addr<kEwramBase||!g.get_memory_data||!g.get_memory_size)return false;
  void*ram=g.get_memory_data(RETRO_MEMORY_SYSTEM_RAM);size_t n=g.get_memory_size(RETRO_MEMORY_SYSTEM_RAM);
  size_t off=(size_t)(addr-kEwramBase);if(!ram||off+sizeof(T)>n)return false;
  std::memcpy(out,(uint8_t*)ram+off,sizeof(T));return true;
}
extern "C" JNIEXPORT jint JNICALL Java_com_showpei_soulgold_m6x1_MainActivity_nativeGetPresentationState(JNIEnv*e,jclass,jintArray out){
  if(!out||e->GetArrayLength(out)<7)return 0;
  uint8_t active=0,battler=0xFF,decrease=0,pal=0,sharp=0,blend=0;int16_t scroll=0;
  if(!m6x1ReadEwramAbs<uint8_t>(M6X1_STAT_ACTIVE_EWRAM_ADDRESS,&active)
   ||!m6x1ReadEwramAbs<uint8_t>(M6X1_STAT_BATTLER_EWRAM_ADDRESS,&battler)
   ||!m6x1ReadEwramAbs<uint8_t>(M6X1_STAT_DECREASE_EWRAM_ADDRESS,&decrease)
   ||!m6x1ReadEwramAbs<uint8_t>(M6X1_STAT_PAL_EWRAM_ADDRESS,&pal)
   ||!m6x1ReadEwramAbs<uint8_t>(M6X1_STAT_SHARP_EWRAM_ADDRESS,&sharp)
   ||!m6x1ReadEwramAbs<uint8_t>(M6X1_STAT_BLEND_EWRAM_ADDRESS,&blend)
   ||!m6x1ReadEwramAbs<int16_t>(M6X1_STAT_SCROLL_EWRAM_ADDRESS,&scroll))return 0;
  jint v[7]={(jint)active,(jint)battler,(jint)decrease,(jint)pal,(jint)sharp,(jint)blend,(jint)scroll};
  e->SetIntArrayRegion(out,0,7,v);return 1;
}
'''
    text=text.replace(anchor,anchor+addition,1)
    path.write_text(text)
    return 'patched'


def patch_java(path:Path):
    text=path.read_text()
    if JAVA_MARKER in text:
        return 'already'
    import_anchor='import android.graphics.Paint;\n'
    if import_anchor not in text: raise SystemExit('Java Paint import anchor missing')
    text=text.replace(import_anchor,import_anchor+'import android.graphics.PorterDuff;\nimport android.graphics.PorterDuffColorFilter;\n',1)

    native_anchor='    static native int nativeGetPlayerProxy(int[] out);\n'
    if native_anchor not in text: raise SystemExit('Java nativeGetPlayerProxy declaration missing')
    text=text.replace(native_anchor,native_anchor+'    static native int nativeGetPresentationState(int[] out);\n',1)

    report_anchor='j.put("showdown_compositor_in_apk",true);j.put("showdown_assets_in_apk",false);j.put("external_pack_required",true);'
    report_repl=('j.put("showdown_compositor_in_apk",true);j.put("showdown_assets_in_apk",false);j.put("external_pack_required",true);'
                 'j.put("presentation_semantics","M6X1_R1_M2R11E_PORT");j.put("hud_bounce_mon_decoupled",true);'
                 'j.put("bottom_ui_restore_frames",gameView.bottomUiRestoreFrames);j.put("stat_showdown_overlay_frames",gameView.statOverlayFrames);')
    if report_anchor not in text: raise SystemExit('Java report anchor missing')
    text=text.replace(report_anchor,report_repl,1)

    fields_anchor='final Paint paint=new Paint();final Paint bootPaint=new Paint(Paint.ANTI_ALIAS_FLAG);final int[]pixels=new int[256*224];final int[]proxy=new int[10];final short[]sourceBuf=new short[4096];'
    fields_repl=('final Paint paint=new Paint();final Paint statPaint=new Paint();final Paint bootPaint=new Paint(Paint.ANTI_ALIAS_FLAG);'
                 'final int[]pixels=new int[256*224];final int[]proxy=new int[10];final int[]presentation=new int[7];final short[]sourceBuf=new short[4096];')
    if fields_anchor not in text: raise SystemExit('RuntimeView field anchor missing')
    text=text.replace(fields_anchor,fields_repl,1)

    counter_anchor='sourceQueueOverHardEvents,overlayFrames,overlayFailures;volatile int sourceQueuePeak,activeSpecies;'
    counter_repl='sourceQueueOverHardEvents,overlayFrames,overlayFailures,bottomUiRestoreFrames,statOverlayFrames;volatile int sourceQueuePeak,activeSpecies;'
    if counter_anchor not in text: raise SystemExit('RuntimeView counter anchor missing')
    text=text.replace(counter_anchor,counter_repl,1)

    ctor_anchor='RuntimeView(){super(MainActivity.this);paint.setFilterBitmap(false);bootPaint.setColor(Color.rgb(120,230,170));'
    ctor_repl='RuntimeView(){super(MainActivity.this);paint.setFilterBitmap(false);statPaint.setFilterBitmap(false);bootPaint.setColor(Color.rgb(120,230,170));'
    if ctor_anchor not in text: raise SystemExit('RuntimeView ctor anchor missing')
    text=text.replace(ctor_anchor,ctor_repl,1)

    reset_anchor='sourceQueueOverHardEvents=overlayFrames=overlayFailures=0;sourceQueuePeak=activeSpecies=0;'
    reset_repl='sourceQueueOverHardEvents=overlayFrames=overlayFailures=bottomUiRestoreFrames=statOverlayFrames=0;sourceQueuePeak=activeSpecies=0;'
    if reset_anchor not in text: raise SystemExit('RuntimeView reset anchor missing')
    text=text.replace(reset_anchor,reset_repl,1)

    old_draw='''        @Override protected void onDraw(Canvas c){super.onDraw(c);if(bmp==null){c.drawText("M6X1 · External Showdown Bridge",42,105,bootPaint);c.drawText("registry + 65536 Hz audio authority",42,145,bootPaint);return;}float sx=getWidth()/(float)bmp.getWidth(),sy=getHeight()/(float)bmp.getHeight(),s=Math.min(sx,sy);int dw=Math.round(bmp.getWidth()*s),dh=Math.round(bmp.getHeight()*s),l=(getWidth()-dw)/2,t=(getHeight()-dh)/2;c.drawBitmap(bmp,null,new Rect(l,t,l+dw,t+dh),paint);if(nativeGetPlayerProxy(proxy)==1){int species=proxy[0];Provider p=providers.get(species);if(p==null){overlayFailures++;activeSpecies=0;return;}Bitmap frame=p.frameAt(SystemClock.uptimeMillis());if(frame==null){overlayFailures++;activeSpecies=species;return;}float cx=l+(proxy[2]+proxy[4])*s,cy=t+(proxy[3]+proxy[5])*s;float fw=frame.getWidth()*p.scale*s,fh=frame.getHeight()*p.scale*s;RectF dst=new RectF(cx-fw/2f,cy-fh/2f,cx+fw/2f,cy+fh/2f);c.drawBitmap(frame,null,dst,paint);overlayFrames++;activeSpecies=species;}else activeSpecies=0;}
'''
    new_draw=r'''        // M6X1_R1_M2R11E_PRESENTATION_PORT
        private boolean bottomBattleUiPresent(int w,int h){
            if(w<32||h<32)return false;int y0=(h*112)/160,light=0,total=0;
            for(int y=y0;y<h;y+=2)for(int x=0;x<w;x+=2){int col=pixels[y*w+x];int r=(col>>>16)&255,g=(col>>>8)&255,b=col&255;if(r>165&&g>165&&b>165)light++;total++;}
            return total>0&&light/(double)total>.16;
        }
        private void restoreBottomBattleUi(Canvas c,int l,int t,float s,int w,int h){
            if(!bottomBattleUiPresent(w,h))return;int y0=(h*112)/160;
            Rect src=new Rect(0,y0,w,h);Rect dst=new Rect(l,t+Math.round(y0*s),l+Math.round(w*s),t+Math.round(h*s));
            c.drawBitmap(bmp,src,dst,paint);bottomUiRestoreFrames++;
        }
        private void drawStatOverlay(Canvas c,Bitmap frame,RectF dst,int battler){
            if(nativeGetPresentationState(presentation)!=1||presentation[0]==0||presentation[1]!=battler||presentation[5]<=0)return;
            final int[][] colors={{255,96,80},{80,150,255},{255,220,80},{80,235,255},{210,100,255},{255,105,220},{90,235,165}};
            int pal=presentation[3],r=220,g=220,b=220;if(pal>=0&&pal<colors.length){r=colors[pal][0];g=colors[pal][1];b=colors[pal][2];}
            int alpha=Math.max(0,Math.min(210,presentation[5]*(presentation[4]!=0?16:14)));
            statPaint.setAlpha(alpha);statPaint.setColorFilter(new PorterDuffColorFilter(Color.rgb(r,g,b),PorterDuff.Mode.ADD));
            int stripe=Math.max(2,Math.round(dst.height()/10f)),gap=Math.max(3,stripe*2),phase=presentation[6]%gap;if(phase<0)phase+=gap;
            for(int y=Math.round(dst.top)-gap+phase;y<dst.bottom;y+=gap){int save=c.save();c.clipRect(dst.left,y,dst.right,Math.min(dst.bottom,y+stripe));c.drawBitmap(frame,null,dst,statPaint);c.restoreToCount(save);}
            statPaint.setAlpha(255);statPaint.setColorFilter(null);statOverlayFrames++;
        }
        @Override protected void onDraw(Canvas c){
            super.onDraw(c);if(bmp==null){c.drawText("M6X1 · External Showdown Bridge",42,105,bootPaint);c.drawText("registry + 65536 Hz audio authority",42,145,bootPaint);return;}
            int bw=bmp.getWidth(),bh=bmp.getHeight();float sx=getWidth()/(float)bw,sy=getHeight()/(float)bh,s=Math.min(sx,sy);int dw=Math.round(bw*s),dh=Math.round(bh*s),l=(getWidth()-dw)/2,t=(getHeight()-dh)/2;
            c.drawBitmap(bmp,null,new Rect(l,t,l+dw,t+dh),paint);
            if(nativeGetPlayerProxy(proxy)==1){
                int species=proxy[0];Provider p=providers.get(species);if(p==null){overlayFailures++;activeSpecies=0;restoreBottomBattleUi(c,l,t,s,bw,bh);return;}
                Bitmap frame=p.frameAt(SystemClock.uptimeMillis());if(frame==null){overlayFailures++;activeSpecies=species;restoreBottomBattleUi(c,l,t,s,bw,bh);return;}
                // R-SD-002 authority: ROM removes action-menu BOUNCE_MON while retaining BOUNCE_HEALTHBOX.
                // x2/y2 therefore remain battler-animation motion, never HUD motion.
                float cx=l+(proxy[2]+proxy[4])*s,cy=t+(proxy[3]+proxy[5])*s;float fw=frame.getWidth()*p.scale*s,fh=frame.getHeight()*p.scale*s;
                RectF dst=new RectF(cx-fw/2f,cy-fh/2f,cx+fw/2f,cy+fh/2f);c.drawBitmap(frame,null,dst,paint);
                drawStatOverlay(c,frame,dst,proxy[1]);overlayFrames++;activeSpecies=species;
            }else activeSpecies=0;
            // R-SD-027 / M2R11E: the lower dialogue/menu UI is final Z authority.
            restoreBottomBattleUi(c,l,t,s,bw,bh);
        }
'''
    if old_draw not in text: raise SystemExit('RuntimeView onDraw authority block missing')
    text=text.replace(old_draw,new_draw,1)
    path.write_text(text)
    return 'patched'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args();root=Path(a.root)
    cpp=patch_cpp(root/'app/src/main/cpp/native_bridge.cpp')
    java=patch_java(root/'app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java')
    print('M6X1_ANDROID_PRESENTATION_PATCH=PASS cpp='+cpp+' java='+java)

if __name__=='__main__':main()
