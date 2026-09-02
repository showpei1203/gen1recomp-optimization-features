package com.showpei.soulgold.m6a1;

import android.app.Activity;
import android.content.Context;
import android.hardware.input.InputManager;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.Choreographer;
import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public final class MainActivity extends Activity implements InputManager.InputDeviceListener {
    private ThorProbeView probe;
    private InputManager inputManager;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        enterImmersive();
        inputManager = (InputManager)getSystemService(Context.INPUT_SERVICE);
        probe = new ThorProbeView(this);
        setContentView(probe);
    }

    @Override protected void onResume() {
        super.onResume();
        enterImmersive();
        inputManager.registerInputDeviceListener(this, null);
        probe.refreshDevices();
        probe.resumeProbe();
    }

    @Override protected void onPause() {
        probe.pauseProbe();
        probe.saveReport("pause");
        inputManager.unregisterInputDeviceListener(this);
        super.onPause();
    }

    @Override protected void onDestroy() {
        probe.close();
        super.onDestroy();
    }

    @Override public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) enterImmersive();
    }

    private void enterImmersive() {
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    private boolean isGameController(InputDevice dev) {
        if (dev == null) return false;
        int s = dev.getSources();
        return (s & InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD ||
               (s & InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK;
    }

    @Override public boolean dispatchKeyEvent(KeyEvent e) {
        InputDevice dev = e.getDevice();
        if (isGameController(dev)) {
            if (probe.handleControllerKey(e)) return true;
        }
        return super.dispatchKeyEvent(e);
    }

    @Override public boolean dispatchGenericMotionEvent(MotionEvent e) {
        InputDevice dev = e.getDevice();
        if (isGameController(dev) && probe.handleJoystick(e)) return true;
        return super.dispatchGenericMotionEvent(e);
    }

    @Override public void onInputDeviceAdded(int deviceId) { probe.refreshDevices(); }
    @Override public void onInputDeviceRemoved(int deviceId) { probe.refreshDevices(); }
    @Override public void onInputDeviceChanged(int deviceId) { probe.refreshDevices(); }

    final class ThorProbeView extends View implements Choreographer.FrameCallback {
        private final Paint titlePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint dimPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint boxPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final ToneGenerator tone = new ToneGenerator(AudioManager.STREAM_MUSIC, 55);
        private final Set<Integer> downKeys = new HashSet<>();
        private final List<String> controllerNames = new ArrayList<>();
        private final long started = SystemClock.elapsedRealtime();
        private boolean running;
        private int keyEvents;
        private int axisEvents;
        private int beepCount;
        private int dpadX;
        private int dpadY;
        private String lastRaw = "尚未收到控制器輸入";
        private String lastMapped = "-";
        private String lastReport = "尚未寫入";
        private float fps;
        private long fpsWindowNs;
        private int fpsFrames;

        ThorProbeView(Context c) {
            super(c);
            setFocusable(true);
            setFocusableInTouchMode(true);
            titlePaint.setColor(Color.rgb(120, 230, 170));
            titlePaint.setTextSize(34f);
            titlePaint.setFakeBoldText(true);
            textPaint.setColor(Color.WHITE);
            textPaint.setTextSize(24f);
            dimPaint.setColor(Color.rgb(180, 190, 195));
            dimPaint.setTextSize(20f);
            boxPaint.setStyle(Paint.Style.STROKE);
            boxPaint.setStrokeWidth(3f);
            boxPaint.setColor(Color.rgb(90, 210, 150));
            setBackgroundColor(Color.rgb(13, 17, 20));
        }

        void resumeProbe() {
            if (!running) {
                running = true;
                fpsWindowNs = 0;
                fpsFrames = 0;
                Choreographer.getInstance().postFrameCallback(this);
            }
        }

        void pauseProbe() { running = false; }
        void close() { running = false; tone.release(); }

        @Override public void doFrame(long frameTimeNanos) {
            if (!running) return;
            if (fpsWindowNs == 0) fpsWindowNs = frameTimeNanos;
            fpsFrames++;
            long dt = frameTimeNanos - fpsWindowNs;
            if (dt >= 1_000_000_000L) {
                fps = (float)(fpsFrames * 1_000_000_000.0 / dt);
                fpsFrames = 0;
                fpsWindowNs = frameTimeNanos;
                invalidate();
            }
            Choreographer.getInstance().postFrameCallback(this);
        }

        void refreshDevices() {
            controllerNames.clear();
            for (int id : InputDevice.getDeviceIds()) {
                InputDevice dev = InputDevice.getDevice(id);
                if (isGameController(dev)) {
                    controllerNames.add(dev.getName() + " [id=" + id + "]");
                }
            }
            invalidate();
        }

        private String mapKey(int code) {
            switch (code) {
                case KeyEvent.KEYCODE_BUTTON_A: return "GBA A";
                case KeyEvent.KEYCODE_BUTTON_B: return "GBA B";
                case KeyEvent.KEYCODE_BUTTON_L1: return "GBA L";
                case KeyEvent.KEYCODE_BUTTON_R1: return "GBA R";
                case KeyEvent.KEYCODE_BUTTON_START: return "START";
                case KeyEvent.KEYCODE_BUTTON_SELECT:
                case KeyEvent.KEYCODE_BACK: return "SELECT";
                case KeyEvent.KEYCODE_DPAD_UP: return "DPAD ↑";
                case KeyEvent.KEYCODE_DPAD_DOWN: return "DPAD ↓";
                case KeyEvent.KEYCODE_DPAD_LEFT: return "DPAD ←";
                case KeyEvent.KEYCODE_DPAD_RIGHT: return "DPAD →";
                default: return "RAW ONLY";
            }
        }

        boolean handleControllerKey(KeyEvent e) {
            int code = e.getKeyCode();
            String mapped = mapKey(code);
            boolean supported = !"RAW ONLY".equals(mapped);
            if (e.getAction() == KeyEvent.ACTION_DOWN && e.getRepeatCount() == 0) {
                downKeys.add(code);
                keyEvents++;
                lastRaw = "KEY down code=" + code + " device=" + e.getDeviceId();
                lastMapped = mapped;
                if (code == KeyEvent.KEYCODE_BUTTON_A) {
                    tone.startTone(ToneGenerator.TONE_PROP_BEEP, 70);
                    beepCount++;
                }
                if (downKeys.contains(KeyEvent.KEYCODE_BUTTON_START) &&
                    (downKeys.contains(KeyEvent.KEYCODE_BUTTON_SELECT) || downKeys.contains(KeyEvent.KEYCODE_BACK))) {
                    saveReport("start_select_combo");
                }
            } else if (e.getAction() == KeyEvent.ACTION_UP) {
                downKeys.remove(code);
                lastRaw = "KEY up code=" + code + " device=" + e.getDeviceId();
                lastMapped = mapped;
            }
            invalidate();
            return supported || code >= KeyEvent.KEYCODE_BUTTON_A;
        }

        boolean handleJoystick(MotionEvent e) {
            if (e.getAction() != MotionEvent.ACTION_MOVE) return false;
            float x = axis(e, MotionEvent.AXIS_X);
            float y = axis(e, MotionEvent.AXIS_Y);
            if (Math.abs(x) < 0.5f) x = 0f;
            if (Math.abs(y) < 0.5f) y = 0f;
            dpadX = x > 0 ? 1 : x < 0 ? -1 : 0;
            dpadY = y > 0 ? 1 : y < 0 ? -1 : 0;
            axisEvents++;
            lastRaw = String.format(Locale.US, "AXIS x=%.2f y=%.2f device=%d", x, y, e.getDeviceId());
            lastMapped = "LEFT STICK → DPAD (threshold 0.50)";
            invalidate();
            return true;
        }

        private float axis(MotionEvent e, int axis) {
            InputDevice dev = e.getDevice();
            InputDevice.MotionRange r = dev == null ? null : dev.getMotionRange(axis, e.getSource());
            if (r == null) return 0f;
            float v = e.getAxisValue(axis);
            return Math.abs(v) > r.getFlat() ? v : 0f;
        }

        void saveReport(String reason) {
            try {
                JSONObject j = new JSONObject();
                j.put("milestone", "M6A1");
                j.put("probe", "AYN_THOR_DEVICE_SMOKE");
                j.put("reason", reason);
                j.put("manufacturer", Build.MANUFACTURER);
                j.put("model", Build.MODEL);
                j.put("device", Build.DEVICE);
                j.put("sdk", Build.VERSION.SDK_INT);
                JSONArray abis = new JSONArray();
                for (String abi : Build.SUPPORTED_ABIS) abis.put(abi);
                j.put("abis", abis);
                JSONArray pads = new JSONArray();
                for (String name : controllerNames) pads.put(name);
                j.put("controllers", pads);
                j.put("key_events", keyEvents);
                j.put("axis_events", axisEvents);
                j.put("audio_beeps", beepCount);
                j.put("fps", fps);
                j.put("last_raw", lastRaw);
                j.put("last_mapped", lastMapped);
                j.put("uptime_ms", SystemClock.elapsedRealtime() - started);
                j.put("rules", new JSONArray().put("R-SD-135").put("R-SD-136").put("R-SD-137").put("R-SD-138"));
                File base = getExternalFilesDir(null);
                if (base == null) base = getFilesDir();
                File out = new File(base, "M6A1_THOR_DEVICE_REPORT.json");
                try (FileOutputStream f = new FileOutputStream(out)) {
                    f.write(j.toString(2).getBytes(StandardCharsets.UTF_8));
                }
                lastReport = out.getAbsolutePath();
            } catch (Exception ex) {
                lastReport = "寫入失敗: " + ex.getClass().getSimpleName() + ": " + ex.getMessage();
            }
            invalidate();
        }

        private void line(Canvas c, String text, float x, float y, Paint p) {
            c.drawText(text, x, y, p);
        }

        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            float w = getWidth();
            float y = 48f;
            line(c, "SoulGold M6A1  ·  AYN THOR Device Smoke", 38f, y, titlePaint);
            y += 42f;
            line(c, "這一版只驗證 THOR 平台層：畫面、FPS、控制器、音訊、儲存。不是 SoulGold gameplay runtime PASS。", 38f, y, dimPaint);
            y += 42f;
            c.drawRect(34f, y - 26f, w - 34f, y + 162f, boxPaint);
            line(c, "裝置：" + Build.MANUFACTURER + " " + Build.MODEL + "   Android API " + Build.VERSION.SDK_INT, 52f, y + 10f, textPaint);
            line(c, "ABI：" + String.join(", ", Build.SUPPORTED_ABIS), 52f, y + 46f, textPaint);
            line(c, String.format(Locale.US, "畫面 callback：%.1f FPS", fps), 52f, y + 82f, textPaint);
            line(c, "控制器：" + (controllerNames.isEmpty() ? "未偵測" : controllerNames.get(0)), 52f, y + 118f, textPaint);
            if (controllerNames.size() > 1) line(c, "其他控制器：" + (controllerNames.size() - 1), 52f, y + 150f, dimPaint);
            y += 210f;

            line(c, "按鍵映射測試", 38f, y, titlePaint);
            y += 40f;
            line(c, "A→GBA A（會嗶一聲）   B→GBA B   L1/R1→L/R   Start→START   Select/Back→SELECT", 38f, y, textPaint);
            y += 34f;
            line(c, "D-pad→方向鍵   左類比→方向鍵 fallback（threshold 0.50）", 38f, y, textPaint);
            y += 42f;
            line(c, "最近原始輸入：" + lastRaw, 38f, y, dimPaint);
            y += 30f;
            line(c, "映射結果：" + lastMapped, 38f, y, dimPaint);
            y += 30f;
            line(c, "KEY events=" + keyEvents + "   AXIS events=" + axisEvents + "   audio beeps=" + beepCount +
                    "   analog dpad=(" + dpadX + "," + dpadY + ")", 38f, y, dimPaint);
            y += 44f;
            line(c, "Start + Select 同時按：寫入 THOR evidence report", 38f, y, textPaint);
            y += 30f;
            line(c, "Report：" + lastReport, 38f, y, dimPaint);
            y += 38f;
            line(c, "驗收目標：無閃退、約 60 FPS、實體按鍵都能被辨識、A 有聲音、report 可寫入。", 38f, y, textPaint);
        }
    }
}
