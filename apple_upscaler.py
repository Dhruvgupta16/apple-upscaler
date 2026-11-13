import os
import sys
import time
import re
import json
import base64
import threading
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
import webview

# =========================================================================
# SILENT SUBPROCESS FLAGS (ZERO CMD WINDOW FLASHES FOR CLI TOOLS)
# =========================================================================
WIN_FLAGS = {}
if sys.platform == "win32":
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    WIN_FLAGS["startupinfo"] = si
    WIN_FLAGS["creationflags"] = subprocess.CREATE_NO_WINDOW

POTPLAYER_PATHS = [
    r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
    r"C:\Program Files\DAUM\PotPlayer\PotPlayer64.exe",
    r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini.exe",
    r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayer.exe"
]

VIDEO_EXTS = ('.mkv', '.mp4', '.avi', '.mov', '.ts', '.webm', '.m2ts', '.flv', '.wmv', '.vob', '.mpg', '.mpeg')
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.jxl')
ALL_SUPPORTED_EXTS = VIDEO_EXTS + IMAGE_EXTS

def find_potplayer():
    for p in POTPLAYER_PATHS:
        if os.path.exists(p):
            return p
    return None

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def load_branding():
    default_branding = {
        "app_name": "Apple Upscaler",
        "app_edition": "Neural Pro",
        "app_version": "2.2.0",
        "app_tagline": "Universal Anime & Film Neural Remastering Studio",
        "window_title": "Apple Upscaler Pro - Universal Anime & Film AI Remaster",
        "author": "Community Open-Source",
        "license": "MIT"
    }
    candidates = [
        os.path.join(get_base_dir(), "branding.json"),
        os.path.join(get_base_dir(), "apple upscaler", "branding.json"),
        os.path.join(os.path.dirname(get_base_dir()), "apple upscaler", "branding.json")
    ]
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        candidates.insert(0, os.path.join(sys._MEIPASS, "branding.json"))
        
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_branding.update(data)
                break
            except Exception:
                pass
    return default_branding

BRANDING = load_branding()

def get_realesrgan_binary():
    candidates = []
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        candidates.append(os.path.join(sys._MEIPASS, "ai_models", "realesrgan-ncnn-vulkan.exe"))
    
    base = get_base_dir()
    candidates.append(os.path.join(base, "ai_models", "realesrgan-ncnn-vulkan.exe"))
    candidates.append(os.path.join(base, "apple upscaler", "ai_models", "realesrgan-ncnn-vulkan.exe"))
    candidates.append(os.path.join(os.path.dirname(base), "apple upscaler", "ai_models", "realesrgan-ncnn-vulkan.exe"))
    
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None

def get_lut_path(filename):
    base = get_base_dir()
    candidates = [
        os.path.join(base, "luts", filename),
        os.path.join(base, "apple upscaler", "luts", filename),
        os.path.join(os.path.dirname(base), "apple upscaler", "luts", filename)
    ]
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        candidates.insert(0, os.path.join(sys._MEIPASS, "luts", filename))
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None

def format_time(seconds):
    if seconds is None or seconds < 0:
        return "00:00:00"
    total_sec = int(float(seconds))
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def parse_time_to_seconds(time_str):
    if not time_str:
        return 0
    parts = time_str.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(time_str)
    except Exception:
        return 0

def probe_media(file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        is_image = ext in IMAGE_EXTS

        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            file_path
        ]
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            **WIN_FLAGS
        )
        if res.returncode != 0 or not res.stdout.strip():
            return None
        data = json.loads(res.stdout)
        
        duration = float(data.get("format", {}).get("duration", 0))
        if is_image:
            duration = 0.0

        info = {
            "path": file_path,
            "filename": os.path.basename(file_path),
            "name": os.path.basename(file_path),
            "size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2),
            "duration": duration,
            "is_image": is_image,
            "media_type": "Photo" if is_image else "Video",
            "video_codec": "unknown",
            "width": 0,
            "height": 0,
            "fps": 24.0 if is_image else 23.976,
            "dar": "16:9",
            "pix_fmt": "yuv420p",
            "color_space": "bt709",
            "total_frames": 1 if is_image else 0,
            "audio_tracks": [],
            "subtitle_tracks": [],
            "status": "Ready",
            "selected_for_batch": True
        }

        for s in data.get("streams", []):
            stype = s.get("codec_type")
            if stype == "video" and info["width"] == 0:
                info["video_codec"] = s.get("codec_name", "unknown")
                info["width"] = int(s.get("width", 0))
                info["height"] = int(s.get("height", 0))
                info["pix_fmt"] = s.get("pix_fmt", "yuv420p")
                info["color_space"] = s.get("color_space") or s.get("color_primaries") or "bt709"
                
                dar = s.get("display_aspect_ratio")
                if dar and ":" in dar:
                    info["dar"] = dar
                elif info["width"] > 0 and info["height"] > 0:
                    ratio = info["width"] / info["height"]
                    if abs(ratio - 16/9) < 0.15:
                        info["dar"] = "16:9"
                    elif abs(ratio - 4/3) < 0.15:
                        info["dar"] = "4:3"
                    elif abs(ratio - 21/9) < 0.15:
                        info["dar"] = "21:9"
                    else:
                        info["dar"] = f"{ratio:.2f}:1"
                
                if not is_image:
                    r_fps = s.get("r_frame_rate", "24/1")
                    if "/" in r_fps:
                        num, den = map(float, r_fps.split("/"))
                        info["fps"] = round(num / max(1.0, den), 3)
                    else:
                        info["fps"] = round(float(r_fps), 3)
                    
                    nb_frames = s.get("nb_frames")
                    if nb_frames and str(nb_frames).isdigit():
                        info["total_frames"] = int(nb_frames)
                    elif info["duration"] > 0 and info["fps"] > 0:
                        info["total_frames"] = int(info["duration"] * info["fps"])

            elif stype == "audio":
                idx = len(info["audio_tracks"])
                lang = s.get("tags", {}).get("language", "und")
                title = s.get("tags", {}).get("title", "")
                codec = s.get("codec_name", "")
                channels = s.get("channels", 2)
                ch_desc = "5.1 Surround" if channels == 6 else ("Stereo 2.0" if channels == 2 else f"{channels}ch")
                track_desc = f"Track #{idx+1}: {lang.upper()} ({codec.upper()} {ch_desc})"
                if title: track_desc += f" - {title}"
                info["audio_tracks"].append(track_desc)

            elif stype == "subtitle":
                idx = len(info["subtitle_tracks"])
                lang = s.get("tags", {}).get("language", "und")
                title = s.get("tags", {}).get("title", "")
                codec = s.get("codec_name", "")
                track_desc = f"Sub #{idx+1}: {lang.upper()} ({codec.upper()})"
                if title: track_desc += f" - {title}"
                info["subtitle_tracks"].append(track_desc)

        return info
    except Exception as e:
        print(f"Probe error: {e}")
        return None

# =========================================================================
# UNIVERSAL AI STUDIO BACKEND CONTROLLER WITH SMART FRAME CACHE
# =========================================================================
class UniversalStudioBackend:
    def __init__(self):
        self.queue = []
        self.active_index = -1
        self.potplayer_exe = find_potplayer()
        self.realesrgan_exe = get_realesrgan_binary()
        self.is_encoding = False
        self.batch_cancel = False
        self.encoding_process = None
        self.start_encode_time = 0
        self.output_dir = ""
        self.custom_lut_path = ""
        self.thread_pool = ThreadPoolExecutor(max_workers=6)
        
        # SMART ZERO-LATENCY FRAME CACHE
        self.cache_dir = os.path.join(tempfile.gettempdir(), "apple_upscaler_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cached_media_path = ""
        self.cached_ts_str = ""
        self.cached_source_file = os.path.join(self.cache_dir, "cached_source.jpg")
        self.cached_ai_scaled_file = os.path.join(self.cache_dir, "cached_ai_scaled.png")
        self.cached_ai_model = ""
        self.cached_b64_source = ""
        
        self.init_environment()

    def init_environment(self):
        app_dir = get_base_dir()
        parent_dir = os.path.dirname(app_dir)

        candidate_dirs = [app_dir]
        if parent_dir and os.path.exists(parent_dir) and parent_dir != app_dir:
            candidate_dirs.append(parent_dir)
        for extra in [
            os.path.join(parent_dir, "apple upscaler studio"),
            os.path.join(app_dir, "apple upscaler studio"),
            r"C:\Users\dhruv\Downloads\apple upscaler studio",
            os.getcwd()
        ]:
            if os.path.exists(extra) and extra not in candidate_dirs:
                candidate_dirs.append(extra)
        
        # Auto-discover video files directly in project directories
        for d in candidate_dirs:
            if os.path.exists(d):
                for f in sorted(os.listdir(d)):
                    if f.lower().endswith(VIDEO_EXTS) and "remaster" not in f.lower() and "sample" not in f.lower() and "preview" not in f.lower():
                        full = os.path.join(d, f)
                        if not any(item["path"] == full for item in self.queue):
                            info = probe_media(full)
                            if info:
                                self.queue.append(info)

        if self.queue and self.active_index == -1:
            self.active_index = 0

        self.output_dir = os.path.join(app_dir, "Remastered_Studio_Output")
        os.makedirs(self.output_dir, exist_ok=True)
        self.ensure_potplayer_shader()

    def ensure_potplayer_shader(self):
        try:
            shader_dir = os.path.expandvars(r"%APPDATA%\PotPlayerMini64\PxShader")
            os.makedirs(shader_dir, exist_ok=True)
            shader_file = os.path.join(shader_dir, "Apple_Upscaler_Remaster.txt")
            code = """// Apple_Upscaler_Remaster=ps_3_0
sampler s0 : register(s0);
float4 p0 : register(c0);
float4 main(float2 tex : TEXCOORD0) : COLOR {
    float4 c0 = tex2D(s0, tex);
    float3 col = saturate((c0.rgb - 0.04) * 1.14);
    col = pow(col, 0.88);
    float gray = dot(col, float3(0.299, 0.587, 0.114));
    col = saturate(lerp(float3(gray, gray, gray), col, 1.26));
    float dx = 1.0 / 1920.0;
    float dy = 1.0 / 1080.0;
    float4 c_up = tex2D(s0, tex + float2(0, -dy));
    float4 c_dn = tex2D(s0, tex + float2(0, dy));
    float4 c_lf = tex2D(s0, tex + float2(-dx, 0));
    float4 c_rt = tex2D(s0, tex + float2(dx, 0));
    float3 blur = (c_up.rgb + c_dn.rgb + c_lf.rgb + c_rt.rgb) * 0.25;
    col = saturate(col + (col - blur) * 0.40);
    return float4(col, c0.a);
}"""
            with open(shader_file, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception:
            pass

    # ================= JS API EXPOSED METHODS =================
    def get_initial_state(self):
        return {
            "queue": self.queue,
            "active_index": self.active_index,
            "output_dir": self.output_dir,
            "potplayer_found": bool(self.potplayer_exe and os.path.exists(self.potplayer_exe)),
            "realesrgan_found": bool(self.realesrgan_exe and os.path.exists(self.realesrgan_exe)),
            "custom_lut_loaded": bool(self.custom_lut_path and os.path.exists(self.custom_lut_path)),
            "branding": BRANDING
        }

    def select_queue_item(self, index):
        if 0 <= index < len(self.queue):
            self.active_index = index
            self.cached_media_path = ""
            self.cached_ts_str = ""
            self.cached_source_file = ""
            self.cached_ai_scaled_file = ""
            self.cached_ai_model = ""
            return self.queue[index]
        return None

    def toggle_queue_item_batch(self, index, selected):
        if 0 <= index < len(self.queue):
            self.queue[index]["selected_for_batch"] = bool(selected)
            return True
        return False

    def select_all_batch(self, selected):
        for item in self.queue:
            item["selected_for_batch"] = bool(selected)
        return self.queue

    def add_files_dialog(self):
        if not webview.windows: return {"queue": self.queue, "active_index": self.active_index}
        win = webview.windows[0]
        file_types = (
            'All Media Files (*.mkv;*.mp4;*.avi;*.mov;*.ts;*.webm;*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff)',
            'Video Files (*.mkv;*.mp4;*.avi;*.mov;*.ts;*.webm)',
            'Photo Files (*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff;*.tif)',
            'All files (*.*)'
        )
        files = win.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types)
        if files:
            new_idx = self.active_index
            for p in files:
                if not any(item["path"] == p for item in self.queue):
                    info = probe_media(p)
                    if info:
                        self.queue.append(info)
                        new_idx = len(self.queue) - 1
            if self.active_index == -1 and self.queue:
                new_idx = 0
            self.active_index = new_idx
        return {"queue": self.queue, "active_index": self.active_index}

    def add_folder_dialog(self):
        if not webview.windows: return {"queue": self.queue, "active_index": self.active_index}
        win = webview.windows[0]
        folder = win.create_file_dialog(webview.FOLDER_DIALOG)
        if folder and len(folder) > 0:
            d = folder[0]
            new_idx = self.active_index
            for f in sorted(os.listdir(d)):
                if f.lower().endswith(ALL_SUPPORTED_EXTS) and "remaster" not in f.lower() and "sample" not in f.lower():
                    full = os.path.join(d, f)
                    if not any(item["path"] == full for item in self.queue):
                        info = probe_media(full)
                        if info:
                            self.queue.append(info)
                            new_idx = len(self.queue) - 1
            if self.active_index == -1 and self.queue:
                new_idx = 0
            self.active_index = new_idx
        return {"queue": self.queue, "active_index": self.active_index}

    def browse_lut_dialog(self):
        if not webview.windows: return ""
        win = webview.windows[0]
        file_types = ('Cube 3D LUT Files (*.cube)', 'All files (*.*)')
        files = win.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if files and len(files) > 0:
            self.custom_lut_path = files[0]
            return os.path.basename(self.custom_lut_path)
        return ""

    def browse_output_dir(self):
        if not webview.windows: return self.output_dir
        win = webview.windows[0]
        folder = win.create_file_dialog(webview.FOLDER_DIALOG)
        if folder and len(folder) > 0:
            self.output_dir = folder[0]
        return self.output_dir

    def open_output_folder(self):
        if self.output_dir and os.path.exists(self.output_dir):
            os.startfile(self.output_dir)
            return True
        return False

    def remove_queue_item(self, index):
        if 0 <= index < len(self.queue):
            del self.queue[index]
            if self.active_index >= len(self.queue):
                self.active_index = len(self.queue) - 1
        return {"queue": self.queue, "active_index": self.active_index}

    # ================= CUSTOM PRESET SAVE / LOAD =================
    def save_preset_dialog(self, settings_json):
        if not webview.windows: return False
        win = webview.windows[0]
        file_types = ('Apple Upscaler Preset (*.applepreset;*.json)', 'All files (*.*)')
        save_path = win.create_file_dialog(webview.SAVE_DIALOG, save_filename="Anime_Custom_Grade.neopreset", file_types=file_types)
        if save_path:
            p = save_path if isinstance(save_path, str) else save_path[0]
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(settings_json)
                return os.path.basename(p)
            except Exception as e:
                print(f"Save preset error: {e}")
        return ""

    def load_preset_dialog(self):
        if not webview.windows: return None
        win = webview.windows[0]
        file_types = ('Apple Upscaler Preset (*.applepreset;*.json)', 'All files (*.*)')
        files = win.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if files and len(files) > 0:
            try:
                with open(files[0], "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {"success": True, "name": os.path.basename(files[0]), "settings": data}
            except Exception as e:
                print(f"Load preset error: {e}")
        return None

    # ================= AI COLOR MATCHING (FROM REFERENCE IMAGE) =================
    def match_color_from_reference_dialog(self, timestamp_sec):
        if self.active_index < 0:
            return None
        if not webview.windows: return None
        
        win = webview.windows[0]
        file_types = ('Reference Images (*.png;*.jpg;*.jpeg;*.webp;*.bmp)', 'All files (*.*)')
        files = win.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if not files or len(files) == 0:
            return None
        
        ref_path = files[0]
        item = self.queue[self.active_index]
        ts_str = "00:00:00" if item.get("is_image") else format_time(timestamp_sec)
        
        try:
            temp_frame = self.cached_source_file if (self.cached_media_path == item["path"] and self.cached_ts_str == ts_str and os.path.exists(self.cached_source_file)) else None
            if not temp_frame:
                temp_frame = os.path.join(tempfile.gettempdir(), f"apple_match_src_{int(time.time()*1000)}.jpg")
                cmd = ["ffmpeg", "-y"]
                if not item.get("is_image"): cmd += ["-ss", ts_str]
                cmd += ["-i", item["path"], "-vframes", "1", "-q:v", "2", temp_frame]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **WIN_FLAGS)

            if not os.path.exists(temp_frame):
                return None

            src_img = Image.open(temp_frame).convert('RGB')
            ref_img = Image.open(ref_path).convert('RGB')

            src = np.array(src_img, dtype=np.float32) / 255.0
            ref = np.array(ref_img, dtype=np.float32) / 255.0

            src_mean = src.mean(axis=(0,1))
            src_std = src.std(axis=(0,1)) + 1e-5
            ref_mean = ref.mean(axis=(0,1))
            ref_std = ref.std(axis=(0,1)) + 1e-5

            contrast_shift = float(ref_std.mean() / src_std.mean())
            bright_shift = float(ref_mean.mean() - src_mean.mean())

            r_diff = float(np.clip((ref_mean[0] - src_mean[0]) * 0.8, -0.35, 0.35))
            g_diff = float(np.clip((ref_mean[1] - src_mean[1]) * 0.8, -0.35, 0.35))
            b_diff = float(np.clip((ref_mean[2] - src_mean[2]) * 0.8, -0.35, 0.35))

            sat_mult = float(np.clip(1.15 * (ref_std.std() / (src_std.std() + 1e-5)), 0.85, 1.55))

            if temp_frame != self.cached_source_file:
                try: os.remove(temp_frame)
                except Exception: pass

            return {
                "success": True,
                "ref_name": os.path.basename(ref_path),
                "contrast": round(float(np.clip(1.10 * contrast_shift, 0.85, 1.45)), 2),
                "brightness": round(float(np.clip(bright_shift * 0.35, -0.05, 0.05)), 3),
                "saturation": round(sat_mult, 2),
                "gamma": 0.88,
                "gain_r": round(r_diff, 2),
                "gain_g": round(g_diff, 2),
                "gain_b": round(b_diff, 2),
                "lift_r": round(r_diff * 0.3, 2),
                "lift_g": round(g_diff * 0.3, 2),
                "lift_b": round(b_diff * 0.3, 2)
            }
        except Exception as e:
            print(f"Color match error: {e}")
            return None

    # ================= FAST AUTO SCENE DETECTION =================
    def detect_scenes_fast(self):
        if self.active_index < 0: return []
        item = self.queue[self.active_index]
        if item.get("is_image") or item["duration"] <= 5:
            return [{"timestamp": "00:00:00", "seconds": 0, "name": "Frame 1"}]

        cmd = [
            "ffmpeg", "-y", "-i", item["path"],
            "-vf", "select='gt(scene,0.38)',scale=160:90,showinfo",
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **WIN_FLAGS)
        
        pts_regex = re.compile(r"pts_time:([\d\.]+)")
        scenes = [{"timestamp": "00:00:00", "seconds": 0, "name": "Intro"}]
        
        for line in res.stderr.splitlines():
            if "showinfo" in line and "pts_time:" in line:
                m = pts_regex.search(line)
                if m:
                    sec = float(m.group(1))
                    if sec - scenes[-1]["seconds"] >= 4.0:
                        scenes.append({
                            "timestamp": format_time(sec),
                            "seconds": int(sec),
                            "name": f"Scene {len(scenes)}"
                        })
            if len(scenes) >= 16:
                break
        return scenes

    # ================= CORE FILTER & RETRO CRT PIPELINE =================
    def build_filter_graph(self, item, settings, for_preview=False):
        contrast = float(settings.get("contrast", 1.140))
        gamma = float(settings.get("gamma", 0.880))
        sat = float(settings.get("saturation", 1.260))
        sharp = float(settings.get("sharpness", 0.800))
        brightness = float(settings.get("brightness", -0.018))
        exposure = float(settings.get("exposure", 0.0))
        
        lift_master = float(settings.get("lift_master", 0.0))
        gamma_master = float(settings.get("gamma_master", 0.0))
        gain_master = float(settings.get("gain_master", 0.0))

        lift_r = float(settings.get("lift_r", 0.0)) + lift_master
        lift_g = float(settings.get("lift_g", 0.0)) + lift_master
        lift_b = float(settings.get("lift_b", 0.0)) + lift_master
        gamma_r = float(settings.get("gamma_r", 0.0)) + gamma_master
        gamma_g = float(settings.get("gamma_g", 0.0)) + gamma_master
        gamma_b = float(settings.get("gamma_b", 0.0)) + gamma_master
        gain_r = float(settings.get("gain_r", 0.0)) + gain_master
        gain_g = float(settings.get("gain_g", 0.0)) + gain_master
        gain_b = float(settings.get("gain_b", 0.0)) + gain_master

        temp = float(settings.get("temp", 0.0))
        tint = float(settings.get("tint", 0.0))
        res_mode = settings.get("resolution", "1080p")
        framing = settings.get("framing", "4:3 Pillarbox")
        edge_clean = settings.get("edge_clean", True)
        denoise = float(settings.get("denoise", 3.0))
        deband = settings.get("deband", True)
        grain = float(settings.get("grain", 0.0))
        deinterlace = settings.get("deinterlace", False)
        lut_mode = settings.get("lut_mode", "none")
        lut_intensity = float(settings.get("lut_intensity", 1.0))
        ai_model = settings.get("ai_model", "realesr-animevideov3")
        
        # RETRO & ANALOG FEATURES
        crt_scanlines = settings.get("crt_scanlines", False)
        crt_intensity = float(settings.get("crt_intensity", 0.35))
        vhs_mode = settings.get("vhs_mode", False)
        vhs_chroma = float(settings.get("vhs_chroma", 2.0))
        line_darken = float(settings.get("line_darken", 0.0))
        cel_deflicker = settings.get("cel_deflicker", False)

        w, h = item["width"], item["height"]
        is_4_3 = (item.get("dar") == "4:3") or (abs(w / max(1, h) - 4/3) < 0.15)
        is_image = item.get("is_image", False)

        if "8K" in res_mode:
            tw_43, th_43 = 5760, 4320
            tw_169, th_169 = 7680, 4320
        elif "4K" in res_mode:
            tw_43, th_43 = 2880, 2160
            tw_169, th_169 = 3840, 2160
        elif "2K" in res_mode or "1440p" in res_mode:
            tw_43, th_43 = 1920, 1440
            tw_169, th_169 = 2560, 1440
        elif "720p" in res_mode:
            tw_43, th_43 = 960, 720
            tw_169, th_169 = 1280, 720
        elif "Match" in res_mode or "Native" in res_mode:
            tw_43, th_43 = w, h
            tw_169, th_169 = w, h
        else:
            tw_43, th_43 = 1440, 1080
            tw_169, th_169 = 1920, 1080

        chain = []

        if deinterlace and not is_image and not for_preview:
            chain.append("yadif=mode=send_frame:parity=auto:deint=all")

        if cel_deflicker and not is_image and not for_preview:
            chain.append("tblend=all_mode=average")

        if edge_clean and w >= 640 and h >= 480 and not for_preview:
            chain.append(f"crop={w-4}:{h-4}:2:2")

        if denoise > 0.1 and not for_preview:
            chain.append(f"hqdn3d=luma_spatial={denoise:.1f}:chroma_spatial={max(1.0, denoise*0.8):.1f}")

        if deband and not for_preview:
            chain.append("deband=range=16:blur=true")

        eff_bright = brightness + (exposure * 0.05)
        eff_gamma = max(0.4, gamma - (exposure * 0.08))
        chain.append(f"eq=contrast={contrast:.3f}:brightness={eff_bright:.3f}:gamma={eff_gamma:.3f}:saturation={sat:.3f}")

        tot_rs = round(lift_r + (temp * 0.005), 3)
        tot_bs = round(lift_b - (temp * 0.005), 3)
        tot_gs = round(lift_g - (tint * 0.005), 3)
        tot_rm = round(gamma_r, 3)
        tot_gm = round(gamma_g, 3)
        tot_bm = round(gamma_b, 3)
        tot_rh = round(gain_r, 3)
        tot_gh = round(gain_g, 3)
        tot_bh = round(gain_b, 3)

        if any(abs(v) > 0.005 for v in [tot_rs, tot_gs, tot_bs, tot_rm, tot_gm, tot_bm, tot_rh, tot_gh, tot_bh]):
            chain.append(f"colorbalance=rs={tot_rs}:gs={tot_gs}:bs={tot_bs}:rm={tot_rm}:gm={tot_gm}:bm={tot_bm}:rh={tot_rh}:gh={tot_gh}:bh={tot_bh}")

        if line_darken > 0.05:
            chain.append(f"unsharp=lx=3:ly=3:la={line_darken*1.2:.2f}:cx=3:cy=3:ca=0.0")

        if sharp > 0.05:
            chain.append(f"cas=strength={sharp:.2f}")

        if grain > 0.01 and not for_preview:
            chain.append(f"noise=alls={int(grain * 25)}:allf=t+u")

        # RETRO CRT SCANLINES & VHS TAPE EFFECT
        if crt_scanlines and not for_preview:
            chain.append(f"drawgrid=width=10000:height=4:thickness=1:color=black@{crt_intensity:.2f}")
            
        if vhs_mode and not for_preview:
            s_val = int(vhs_chroma)
            chain.append(f"rgbashift=rh={-s_val}:bh={s_val}:rv=1:bv=-1")

        lut_file = None
        if lut_mode == "custom" and self.custom_lut_path and os.path.exists(self.custom_lut_path):
            lut_file = self.custom_lut_path
        elif lut_mode == "cel_master":
            lut_file = get_lut_path("Anime_Cel_Master.cube")
        elif lut_mode == "cinema_35mm":
            lut_file = get_lut_path("Cinema_Vibrant_35mm.cube")

        is_complex = False
        scale_flag = "spline" if "spline" in ai_model else ("lanczos" if not for_preview else "bilinear")

        if lut_file:
            safe_lut = lut_file.replace("\\", "/").replace(":", "\\:")
            core = ",".join(chain) if chain else "null"
            if lut_intensity >= 0.98:
                chain.append(f"lut3d=file='{safe_lut}':interp=tetrahedral")
            else:
                lut_branch = (
                    f"[0:v]{core},split=2[orig][tolut];"
                    f"[tolut]lut3d=file='{safe_lut}':interp=tetrahedral[luted];"
                    f"[orig][luted]blend=all_mode=normal:all_opacity={lut_intensity:.2f}[v_graded]"
                )
                if is_4_3 and "Ambient" in framing and not is_image and not for_preview:
                    filter_str = (
                        f"{lut_branch};"
                        f"[v_graded]split=2[fg][bg];"
                        f"[bg]scale=64:36,scale={tw_169}:{th_169}:flags=bilinear[bg_blur];"
                        f"[fg]scale={tw_43}:{th_43}:flags={scale_flag}[fg_scaled];"
                        f"[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2"
                    )
                else:
                    target_w = tw_43 if is_4_3 else tw_169
                    target_h = th_43 if is_4_3 else th_169
                    filter_str = f"{lut_branch};[v_graded]scale={target_w}:{target_h}:flags={scale_flag}"
                is_complex = True
                canvas_w = tw_169 if (is_4_3 and "Ambient" in framing) else (tw_43 if is_4_3 else tw_169)
                canvas_h = th_169 if (is_4_3 and "Ambient" in framing) else (th_43 if is_4_3 else th_169)
                return filter_str, is_complex, canvas_w, canvas_h

        if is_4_3 and "Ambient" in framing and not is_image and not for_preview:
            core = ",".join(chain)
            filter_str = (
                f"[0:v]{core},split=2[fg][bg];"
                f"[bg]scale=64:36,scale={tw_169}:{th_169}:flags=bilinear[bg_blur];"
                f"[fg]scale={tw_43}:{th_43}:flags={scale_flag}[fg_scaled];"
                f"[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2"
            )
            is_complex = True
            canvas_w, canvas_h = tw_169, th_169
        elif is_4_3 and "Crop" in framing and not is_image:
            crop_h = int(w * 9 / 16)
            crop_y = int((h - crop_h) / 2)
            chain.insert(0, f"crop={w}:{crop_h}:0:{crop_y}")
            chain.append(f"scale={tw_169}:{th_169}:flags={scale_flag}")
            filter_str = ",".join(chain)
            canvas_w, canvas_h = tw_169, th_169
        else:
            if is_4_3 and not is_image:
                chain.append(f"scale={tw_43}:{th_43}:flags={scale_flag}")
                canvas_w, canvas_h = tw_43, th_43
            else:
                chain.append(f"scale={tw_169}:{th_169}:flags={scale_flag}")
                canvas_w, canvas_h = tw_169, th_169
            filter_str = ",".join(chain)

        return filter_str, is_complex, canvas_w, canvas_h

    # ================= ZERO-LATENCY HIGH PRECISION PREVIEW =================
    def extract_preview_frames(self, timestamp_sec, settings):
        if self.active_index < 0 or self.active_index >= len(self.queue):
            return None
        item = self.queue[self.active_index]
        in_path = item["path"]
        is_image = item.get("is_image", False)
        ts_str = "00:00:00" if is_image else format_time(timestamp_sec)
        ai_model = settings.get("ai_model", "realesr-animevideov3")

        # 1. SMART BASE-FRAME CACHING (ONLY SEEK VIDEO OR RUN AI WHEN TIMESTAMP CHANGES)
        need_source_extract = (
            self.cached_media_path != in_path or
            self.cached_ts_str != ts_str or
            not os.path.exists(self.cached_source_file)
        )

        if need_source_extract:
            cmd_b = ["ffmpeg", "-y"]
            if not is_image: cmd_b += ["-ss", ts_str]
            cmd_b += [
                "-i", in_path,
                "-vframes", "1", "-an", "-sn",
                "-f", "image2", "-c:v", "mjpeg", "-q:v", "2",
                self.cached_source_file
            ]
            subprocess.run(cmd_b, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **WIN_FLAGS)
            
            if os.path.exists(self.cached_source_file):
                with open(self.cached_source_file, "rb") as f:
                    self.cached_b64_source = base64.b64encode(f.read()).decode("ascii")
            
            self.cached_media_path = in_path
            self.cached_ts_str = ts_str
            self.cached_ai_model = ""

        # 2. NEURAL UPSCALING CACHE (ONLY RUNS ONCE PER TIMESTAMP OR MODEL CHANGE)
        if "realesr" in ai_model and self.realesrgan_exe and os.path.exists(self.realesrgan_exe):
            need_ai_run = (self.cached_ai_model != ai_model or not os.path.exists(self.cached_ai_scaled_file))
            if need_ai_run and os.path.exists(self.cached_source_file):
                m_arg = "realesr-animevideov3" if "videov3" in ai_model else "realesrgan-x4plus-anime"
                s_arg = "2" if "videov3" in ai_model else "4"
                m_dir = os.path.join(os.path.dirname(self.realesrgan_exe), "models")
                
                cmd_ai = [
                    self.realesrgan_exe,
                    "-i", self.cached_source_file,
                    "-o", self.cached_ai_scaled_file,
                    "-m", m_dir,
                    "-n", m_arg,
                    "-s", s_arg,
                    "-g", "0",
                    "-j", "2:2:2"
                ]
                subprocess.run(cmd_ai, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **WIN_FLAGS)
                self.cached_ai_model = ai_model

        # 3. FAST 20MS IN-MEMORY COLOR GRADING ON CACHED FRAME
        base_input = self.cached_ai_scaled_file if ("realesr" in ai_model and os.path.exists(self.cached_ai_scaled_file)) else self.cached_source_file
        if not os.path.exists(base_input):
            base_input = in_path

        filter_str, is_complex, target_w, target_h = self.build_filter_graph(item, settings, for_preview=True)

        cmd_a = ["ffmpeg", "-y", "-i", base_input]
        if is_complex: cmd_a += ["-filter_complex", filter_str]
        else: cmd_a += ["-vf", filter_str]
        cmd_a += [
            "-vframes", "1", "-an", "-sn",
            "-f", "image2", "-c:v", "mjpeg", "-q:v", "2", "pipe:1"
        ]
        res_a = subprocess.run(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, **WIN_FLAGS)
        b64_a = base64.b64encode(res_a.stdout).decode("ascii") if res_a.stdout else ""

        return {
            "before": f"data:image/jpeg;base64,{self.cached_b64_source}",
            "after": f"data:image/jpeg;base64,{b64_a}",
            "timestamp": ts_str,
            "width": target_w,
            "height": target_h
        }

    # ================= A/B MODEL COMPARISON (REAL-ESRGAN VS LANCZOS) =================
    def get_ab_model_comparison(self, timestamp_sec, settings):
        if self.active_index < 0: return None
        item = self.queue[self.active_index]

        ai_settings = dict(settings)
        ai_settings["ai_model"] = "realesr-animevideov3"
        res_ai = self.extract_preview_frames(timestamp_sec, ai_settings)

        lanczos_settings = dict(settings)
        lanczos_settings["ai_model"] = "lanczos"
        res_lanczos = self.extract_preview_frames(timestamp_sec, lanczos_settings)

        return {
            "model_a": res_ai.get("after") if res_ai else "",
            "model_b": res_lanczos.get("after") if res_lanczos else "",
            "name_a": "Real-ESRGAN Neural AI",
            "name_b": "Lanczos-3 Sinc Scaler"
        }

    # ================= PARALLEL VISUAL AUDITION (SUGGEST ENHANCEMENTS - BUG FIXED) =================
    def get_preset_auditions(self, timestamp_sec):
        if self.active_index < 0:
            return []
        item = self.queue[self.active_index]
        is_image = item.get("is_image", False)
        ts_str = "00:00:00" if is_image else format_time(timestamp_sec)

        # 1. Guarantee base frame is extracted at current timestamp
        if not os.path.exists(self.cached_source_file) or self.cached_media_path != item["path"] or self.cached_ts_str != ts_str:
            cmd_b = ["ffmpeg", "-y"]
            if not is_image: cmd_b += ["-ss", ts_str]
            cmd_b += ["-i", item["path"], "-vframes", "1", "-an", "-sn", "-f", "image2", "-c:v", "mjpeg", "-q:v", "2", self.cached_source_file]
            subprocess.run(cmd_b, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **WIN_FLAGS)
            self.cached_media_path = item["path"]
            self.cached_ts_str = ts_str

        base_input = self.cached_source_file
        if not os.path.exists(base_input):
            return []

        presets = [
            {
                "id": "cel_master",
                "name": "Reference Cel Master",
                "tag": "Balanced Reference",
                "desc": "Telecine black restoration, deep saturation, AMD CAS 0.80 line clarity.",
                "settings": {"contrast": 1.140, "brightness": -0.018, "gamma": 0.880, "saturation": 1.260, "sharpness": 0.80, "denoise": 3.0, "temp": 0, "exposure": 0.0, "crt_scanlines": False, "vhs_mode": False}
            },
            {
                "id": "film_35mm",
                "name": "35mm Analog Film",
                "tag": "Cinematic Warm",
                "desc": "Warm analog color temperature, fine 35mm grain, soft highlight knee.",
                "settings": {"contrast": 1.080, "brightness": -0.010, "gamma": 0.940, "saturation": 1.120, "sharpness": 0.50, "denoise": 1.5, "temp": 14, "exposure": 0.0, "crt_scanlines": False, "vhs_mode": False}
            },
            {
                "id": "ink_sharp",
                "name": "Ink Outline 4K",
                "tag": "Max Definition",
                "desc": "Full CAS 1.00 sharpness with cel artifact smoothing for 4K display.",
                "settings": {"contrast": 1.180, "brightness": -0.020, "gamma": 0.860, "saturation": 1.220, "sharpness": 1.00, "denoise": 4.5, "temp": 0, "exposure": 0.0, "crt_scanlines": False, "vhs_mode": False}
            },
            {
                "id": "hdr_pop",
                "name": "Dynamic HDR Punch",
                "tag": "Punchy Contrast",
                "desc": "Deep inky shadows, punchy contrast ratio, vivid saturated primaries.",
                "settings": {"contrast": 1.250, "brightness": -0.028, "gamma": 0.840, "saturation": 1.380, "sharpness": 0.85, "denoise": 2.5, "temp": 0, "exposure": 0.1, "crt_scanlines": False, "vhs_mode": False}
            },
            {
                "id": "retro_crt",
                "name": "90s CRT Broadcast",
                "tag": "Retro Nostalgia",
                "desc": "Phosphor scanlines, subtle curved screen glass, authentic TV blooming.",
                "settings": {"contrast": 1.120, "brightness": 0.005, "gamma": 0.900, "saturation": 1.320, "sharpness": 0.60, "denoise": 2.0, "temp": 8, "exposure": 0.0, "crt_scanlines": True, "vhs_mode": False}
            },
            {
                "id": "oled_clean",
                "name": "Modern OLED Clean",
                "tag": "Zero Banding",
                "desc": "Pristine debanded gradients, cool neutral whites, clean modern edge art.",
                "settings": {"contrast": 1.160, "brightness": -0.015, "gamma": 0.880, "saturation": 1.180, "sharpness": 0.80, "denoise": 3.5, "temp": -10, "exposure": 0.0, "crt_scanlines": False, "vhs_mode": False}
            }
        ]

        def render_preset(p):
            try:
                s = p["settings"]
                c = float(s.get("contrast", 1.14))
                b = float(s.get("brightness", -0.018))
                g = float(s.get("gamma", 0.88))
                sat = float(s.get("saturation", 1.26))
                sharp = float(s.get("sharpness", 0.80))
                temp = float(s.get("temp", 0.0))
                
                chain = [
                    f"eq=contrast={c:.2f}:brightness={b:.3f}:gamma={g:.2f}:saturation={sat:.2f}",
                    f"scale=360:-2:flags=bilinear"
                ]
                if abs(temp) > 1:
                    chain.append(f"colorbalance=rs={temp*0.005:.3f}:bs={-temp*0.005:.3f}")
                if sharp > 0.1:
                    chain.append(f"cas=strength={sharp:.2f}")
                if s.get("crt_scanlines"):
                    chain.append("drawgrid=width=10000:height=4:thickness=1:color=black@0.4")
                
                vf_str = ",".join(chain)
                cmd = [
                    "ffmpeg", "-y", "-i", base_input,
                    "-vf", vf_str,
                    "-vframes", "1", "-an", "-sn",
                    "-f", "image2", "-c:v", "mjpeg", "-q:v", "4", "pipe:1"
                ]
                r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, **WIN_FLAGS)
                b64 = base64.b64encode(r.stdout).decode("ascii") if r.stdout else ""
                return {
                    "id": p["id"],
                    "name": p["name"],
                    "tag": p["tag"],
                    "desc": p["desc"],
                    "settings": p["settings"],
                    "thumb": f"data:image/jpeg;base64,{b64}" if b64 else ""
                }
            except Exception as e:
                print(f"Audition error: {e}")
                return None

        results = list(self.thread_pool.map(render_preset, presets))
        return [r for r in results if r and r.get("thumb")]

    # ================= REAL COLOR-GRADED POTPLAYER / SAMPLE WATCH =================
    def watch_in_potplayer_color_graded(self, timestamp_sec, settings, duration_sec=30):
        if self.active_index < 0:
            return {"status": "error", "message": "No active media selected"}
        
        item = self.queue[self.active_index]
        is_image = item.get("is_image", False)
        ts_str = "00:00:00" if is_image else format_time(timestamp_sec)
        
        temp_dir = tempfile.gettempdir()
        sample_out = os.path.join(temp_dir, f"apple_remaster_preview_{int(time.time()*1000)}.mkv")
        
        filter_str, is_complex, _, _ = self.build_filter_graph(item, settings)

        def worker():
            cmd = ["ffmpeg", "-y"]
            if not is_image: cmd += ["-ss", ts_str]
            cmd += ["-i", item["path"]]
            if not is_image: cmd += ["-t", str(duration_sec)]

            if is_complex: cmd += ["-filter_complex", filter_str]
            else: cmd += ["-vf", filter_str]

            cmd += [
                "-c:v", "hevc_nvenc", "-preset", "p1", "-cq", "20", "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                "-c:s", "copy",
                sample_out
            ]

            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **WIN_FLAGS)
            
            if os.path.exists(sample_out) and os.path.getsize(sample_out) > 50000:
                if self.potplayer_exe and os.path.exists(self.potplayer_exe):
                    subprocess.Popen([self.potplayer_exe, sample_out])
                else:
                    os.startfile(sample_out)
                if webview.windows:
                    webview.windows[0].evaluate_js("onPotPlayerLaunched(true, 'Playing remastered sample with dual-audio & subtitles in PotPlayer')")
            else:
                if webview.windows:
                    webview.windows[0].evaluate_js("onPotPlayerLaunched(false, 'Preview encode failed')")

        threading.Thread(target=worker, daemon=True).start()
        return {"status": "ok", "message": "Rendering live color-graded sample..."}

    # ================= BATCH PROCESSING QUEUE ENGINE =================
    def start_batch_encode(self, settings):
        if self.is_encoding or not self.queue:
            return False

        batch_items = [item for item in self.queue if item.get("selected_for_batch", True)]
        if not batch_items:
            batch_items = self.queue

        self.is_encoding = True
        self.batch_cancel = False

        def worker():
            out_dir = self.output_dir
            total_items = len(batch_items)
            cq_val = str(settings.get("cq", 20))
            gpu_mode = settings.get("gpu", "nvenc_hevc")
            export_fmt = settings.get("export_fmt", "mkv").lower()
            photo_fmt = settings.get("photo_fmt", "png").lower()
            audio_mode = settings.get("audio_mode", "copy")
            sub_mode = settings.get("sub_mode", "copy")
            trim_enabled = settings.get("trim_enabled", False)
            trim_in = parse_time_to_seconds(settings.get("trim_in", "00:00:00"))
            trim_out = parse_time_to_seconds(settings.get("trim_out", "00:00:00"))
            delete_orig = settings.get("delete_original", False)
            ai_model = settings.get("ai_model", "realesr-animevideov3")
            audio_eq = settings.get("audio_eq", False)

            if "av1" in gpu_mode: vcodec = "av1_nvenc"
            elif "h264" in gpu_mode: vcodec = "h264_nvenc"
            elif "cpu" in gpu_mode: vcodec = "libx265"
            else: vcodec = "hevc_nvenc"

            for idx, item in enumerate(batch_items):
                if self.batch_cancel: break

                fname = os.path.splitext(item["filename"])[0].replace("$$", "").strip()
                res_tag = settings.get("resolution", "1080p")
                is_image = item.get("is_image", False)

                if is_image:
                    out_file = os.path.join(out_dir, f"{fname} [{res_tag} Remaster].{photo_fmt}")
                else:
                    out_file = os.path.join(out_dir, f"{fname} [{res_tag} Remaster].{export_fmt}")

                filter_str, is_complex, _, _ = self.build_filter_graph(item, settings)
                
                total_frames = max(1, item["total_frames"])
                if not is_image and trim_enabled and trim_out > trim_in:
                    total_frames = max(1, int((trim_out - trim_in) * item["fps"]))

                self.start_encode_time = time.time()

                if is_image:
                    if "realesr" in ai_model and self.realesrgan_exe and os.path.exists(self.realesrgan_exe):
                        temp_pre = os.path.join(tempfile.gettempdir(), f"apple_exp_in_{int(time.time()*1000)}.png")
                        cmd_p = ["ffmpeg", "-y", "-i", item["path"]]
                        if is_complex: cmd_p += ["-filter_complex", filter_str]
                        else: cmd_p += ["-vf", filter_str]
                        cmd_p += ["-c:v", "png", temp_pre]
                        subprocess.run(cmd_p, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **WIN_FLAGS)

                        if os.path.exists(temp_pre):
                            m_arg = "realesr-animevideov3" if "videov3" in ai_model else "realesrgan-x4plus-anime"
                            s_arg = "2" if "videov3" in ai_model else "4"
                            m_dir = os.path.join(os.path.dirname(self.realesrgan_exe), "models")
                            cmd_r = [
                                self.realesrgan_exe,
                                "-i", temp_pre,
                                "-o", out_file,
                                "-m", m_dir,
                                "-n", m_arg,
                                "-s", s_arg,
                                "-g", "0",
                                "-j", "2:2:2"
                            ]
                            subprocess.run(cmd_r, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **WIN_FLAGS)
                            try: os.remove(temp_pre)
                            except Exception: pass
                    else:
                        cmd = ["ffmpeg", "-y", "-i", item["path"]]
                        if is_complex: cmd += ["-filter_complex", filter_str]
                        else: cmd += ["-vf", filter_str]
                        
                        if photo_fmt == "png": cmd += ["-c:v", "png"]
                        elif photo_fmt in ("jpg", "jpeg"): cmd += ["-c:v", "mjpeg", "-q:v", "1"]
                        elif photo_fmt == "webp": cmd += ["-c:v", "libwebp", "-lossless", "1"]
                        elif photo_fmt in ("tif", "tiff"): cmd += ["-c:v", "tiff"]
                        cmd += [out_file]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **WIN_FLAGS)
                else:
                    cmd = ["ffmpeg", "-y"]
                    if "nvenc" in vcodec: cmd += ["-hwaccel", "cuda"]

                    if trim_enabled and trim_in > 0: cmd += ["-ss", format_time(trim_in)]
                    cmd += ["-i", item["path"]]
                    if trim_enabled and trim_out > trim_in: cmd += ["-t", str(trim_out - trim_in)]

                    if is_complex: cmd += ["-filter_complex", filter_str]
                    else: cmd += ["-vf", filter_str]

                    cmd += ["-c:v", vcodec, "-pix_fmt", "yuv420p"]
                    if "nvenc" in vcodec:
                        cmd += ["-preset", "p2", "-cq", cq_val, "-spatial-aq", "1", "-temporal-aq", "1"]
                    else:
                        cmd += ["-crf", cq_val, "-preset", "medium"]

                    # Dialogue Presence EQ & Hiss Filter
                    if audio_eq:
                        cmd += ["-af", "afftdn=nf=-25,equalizer=f=3000:width_type=h:width=1000:g=3.5"]

                    if audio_mode == "aac" or export_fmt in ("mp4", "mov"):
                        cmd += ["-c:a", "aac", "-b:a", "320k"]
                    else:
                        cmd += ["-c:a", "copy"]

                    if sub_mode == "none" or export_fmt in ("mp4", "mov"):
                        cmd += ["-sn"]
                    else:
                        cmd += ["-c:s", "copy"]

                    cmd += [out_file]

                    self.encoding_process = subprocess.Popen(
                        cmd,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1,
                        encoding="utf-8",
                        errors="replace",
                        **WIN_FLAGS
                    )

                    frame_regex = re.compile(r"frame=\s*(\d+)")
                    fps_regex = re.compile(r"fps=\s*([\d\.]+)")

                    for line in self.encoding_process.stderr:
                        if self.batch_cancel: break
                        if "frame=" in line:
                            fm = frame_regex.search(line)
                            fpm = fps_regex.search(line)
                            if fm:
                                curr_f = int(fm.group(1))
                                pct = round(min(100.0, (curr_f / total_frames) * 100), 1)
                                fps = float(fpm.group(1)) if fpm else 95.0
                                elapsed = time.time() - self.start_encode_time
                                rem_sec = int((total_frames - curr_f) / max(0.1, fps)) if curr_f < total_frames else 0

                                telemetry = {
                                    "file_index": idx + 1,
                                    "total_files": total_items,
                                    "filename": item["filename"],
                                    "percent": pct,
                                    "fps": round(fps, 1),
                                    "multiplier": round(fps / max(1.0, item["fps"]), 1),
                                    "elapsed": format_time(elapsed),
                                    "eta": format_time(rem_sec),
                                    "frame": curr_f,
                                    "total_frames": total_frames
                                }
                                if webview.windows:
                                    webview.windows[0].evaluate_js(f"onBatchProgress({json.dumps(telemetry)})")

                    self.encoding_process.wait()

                item_done = os.path.exists(out_file) and os.path.getsize(out_file) > 10000

                if item_done and delete_orig and not self.batch_cancel:
                    try:
                        if os.path.exists(item["path"]) and os.path.abspath(item["path"]) != os.path.abspath(out_file):
                            os.remove(item["path"])
                    except Exception as e:
                        print(f"Error removing original file: {e}")

                if webview.windows:
                    webview.windows[0].evaluate_js(f"onFileCompleted({idx}, {json.dumps(item_done)})")

            self.is_encoding = False
            if webview.windows:
                webview.windows[0].evaluate_js(f"onBatchFinished({json.dumps(not self.batch_cancel)})")

        threading.Thread(target=worker, daemon=True).start()
        return True

    def stop_batch_encode(self):
        if self.is_encoding:
            self.batch_cancel = True
            if self.encoding_process:
                try: self.encoding_process.terminate()
                except Exception: pass
            self.is_encoding = False
            return True
        return False

# =========================================================================
# REFINED STUDIO PRO INTERFACE (SLEEK MODERN PALETTE & CRT SHADING)
# =========================================================================
HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Apple Upscaler Pro</title>
<style>
:root {
  --bg-app: #0c090a;
  --bg-surface: #140d10;
  --bg-panel: #1a1115;
  --bg-elevated: #24161c;
  --bg-input: #2e1a22;
  --border-subtle: rgba(244, 63, 94, 0.12);
  --border-bright: rgba(244, 63, 94, 0.28);
  
  --accent-primary: #e11d48;
  --accent-primary-hover: #f43f5e;
  --accent-glow: rgba(225, 29, 72, 0.35);
  --accent-ruby: #fb7185;
  --accent-cyan: #38bdf8;
  --accent-emerald: #10b981;
  --accent-amber: #f59e0b;
  --accent-rose: #f43f5e;
  
  --text-main: #fff1f2;
  --text-sub: #fda4af;
  --text-dim: #9f7582;
  
  --font-sans: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, system-ui, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
  
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-pill: 9999px;
  
  --ease-fluid: cubic-bezier(0.16, 1, 0.3, 1);
}

* { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }

body {
  background: var(--bg-app);
  color: var(--text-main);
  font-family: var(--font-sans);
  height: 100vh;
  display: flex;
  overflow: hidden;
  font-size: 13px;
  line-height: 1.4;
  -webkit-font-smoothing: antialiased;
}

.app-shell {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* MAIN STAGE */
.stage-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-app);
  position: relative;
}

/* TOPBAR */
.topbar {
  height: 54px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  z-index: 10;
}
.brand-group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-logo {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #e11d48, #38bdf8);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(82, 70, 234, 0.35);
}
.brand-title {
  font-weight: 700;
  font-size: 14px;
  letter-spacing: -0.2px;
  color: #ffffff;
}
.brand-badge {
  font-size: 10px;
  font-weight: 700;
  color: #c7d2fe;
  background: rgba(82, 70, 234, 0.2);
  border: 1px solid rgba(82, 70, 234, 0.4);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

/* FOLDER VIDEO NAVIGATION ARROWS */
.folder-nav-group {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  margin-left: 10px;
}
.btn-nav-arrow {
  background: transparent;
  border: none;
  color: var(--text-sub);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-nav-arrow:hover {
  background: var(--bg-input);
  color: #ffffff;
}
.lbl-nav-counter {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
  padding: 0 4px;
  font-family: var(--font-mono);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.btn-action {
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  color: var(--text-main);
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s var(--ease-fluid);
}
.btn-action:hover {
  background: var(--bg-elevated);
  border-color: var(--border-bright);
  transform: translateY(-1px);
}
.btn-action.suggest {
  background: rgba(82, 70, 234, 0.15);
  border-color: rgba(82, 70, 234, 0.5);
  color: #c7d2fe;
}
.btn-action.suggest:hover {
  background: var(--accent-primary);
  color: #ffffff;
  box-shadow: 0 0 20px rgba(82, 70, 234, 0.45);
}

/* VIEWPORT AREA */
.viewport-area {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  overflow: hidden;
  background: radial-gradient(circle at center, #11131c 0%, #06070a 100%);
}

.viewmode-pill {
  position: absolute;
  top: 18px;
  z-index: 30;
  background: rgba(16, 18, 26, 0.92);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-bright);
  padding: 3px;
  border-radius: var(--radius-pill);
  display: flex;
  gap: 2px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.6);
}
.tab-pill {
  background: transparent;
  border: none;
  color: var(--text-sub);
  font-size: 11px;
  font-weight: 600;
  padding: 5px 14px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all 0.2s var(--ease-fluid);
}
.tab-pill.active {
  background: var(--accent-primary);
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(82, 70, 234, 0.4);
}

/* CANVAS BOUNDS */
.canvas-bounds {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  max-width: 100%;
  max-height: calc(100vh - 180px);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.85);
  overflow: hidden;
  background: #000000;
  cursor: ew-resize;
  transition: transform 0.25s var(--ease-fluid), border-radius 0.25s ease;
}
.canvas-bounds.zoom-100 {
  cursor: grab;
  transform: scale(1.6);
}
.canvas-bounds.crt-curved {
  transform: perspective(700px) scale(0.96);
  border-radius: 36px !important;
  box-shadow: inset 0 0 90px rgba(0,0,0,0.85), 0 0 40px rgba(0,0,0,0.95);
}

img:not([src]), img[src=""], img[src="#"] {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
}

.layer-before {
  display: none;
  max-width: 100%;
  max-height: calc(100vh - 180px);
  width: auto;
  height: auto;
  object-fit: contain;
  opacity: 0;
  transition: opacity 0.2s var(--ease-fluid);
  pointer-events: none;
  background: transparent;
}
.layer-before:not([src]), .layer-after:not([src]) {
  display: none !important;
}

.layer-after-clip {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  clip-path: inset(0 0 0 50%);
  pointer-events: none;
}
.layer-after {
  display: none;
  width: 100%;
  height: 100%;
  object-fit: contain;
  opacity: 0;
  transition: opacity 0.2s var(--ease-fluid);
  will-change: filter;
  background: transparent;
}

/* RETRO CRT SCANLINE OVERLAY */
/* AUTHENTIC TRINITRON APERTURE GRILLE & PHOSPHOR TRIAD CRT OVERLAY */
.crt-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none;
  z-index: 22;
  display: none;
  background: 
    linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.55) 50%),
    linear-gradient(90deg, rgba(255, 0, 0, 0.08), rgba(0, 255, 0, 0.04), rgba(0, 0, 255, 0.08));
  background-size: 100% 3px, 3px 100%;
  box-shadow: inset 0 0 90px rgba(0, 0, 0, 0.7);
}

.crt-curved {
  border-radius: 18px !important;
  box-shadow: inset 0 0 120px rgba(0, 0, 0, 0.85), 0 0 35px rgba(0, 0, 0, 0.9) !important;
  transform: perspective(600px) scale(0.985);
  overflow: hidden !important;
}

/* AUTHENTIC NTSC VHS HELICAL SCAN HEAD-SWITCHING TRACKING BAND */
.vhs-tracking-band {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 22px;
  pointer-events: none;
  z-index: 23;
  display: none;
  background: repeating-linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.45) 0px,
    rgba(20, 20, 20, 0.90) 3px,
    rgba(220, 220, 220, 0.60) 7px,
    rgba(10, 10, 10, 0.85) 12px,
    rgba(255, 255, 255, 0.70) 16px,
    rgba(30, 30, 30, 0.95) 22px
  );
  mix-blend-mode: hard-light;
  animation: vhsHeadSwitching 0.12s steps(4) infinite alternate;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.8);
  opacity: 0.85;
}

@keyframes vhsHeadSwitching {
  0% { transform: translateY(0px) scaleX(1.0); filter: contrast(200%) brightness(120%); }
  50% { transform: translateY(-2px) scaleX(1.02); filter: contrast(180%) brightness(140%); }
  100% { transform: translateY(1px) scaleX(0.98); filter: contrast(240%) brightness(110%); }
}

.vhs-jitter {
  animation: ntscTapeJitter 0.18s steps(2) infinite;
}

@keyframes ntscTapeJitter {
  0% { transform: translate(0, 0); }
  25% { transform: translate(-0.75px, 0.25px); }
  50% { transform: translate(0.5px, -0.25px); }
  75% { transform: translate(-0.25px, 0); }
  100% { transform: translate(0.5px, 0); }
}

.select-nav-media {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  color: var(--text-main);
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  outline: none;
  cursor: pointer;
  max-width: 220px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.select-nav-media:hover, .select-nav-media:focus {
  border-color: var(--accent-primary);
}

/* CURTAIN DIVIDER */
.curtain-divider {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 2px;
  background: #ffffff;
  cursor: ew-resize;
  z-index: 25;
  display: none;
  pointer-events: none;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
}
.curtain-knob {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 30px;
  height: 30px;
  background: #151722;
  border: 2px solid #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.9);
  pointer-events: all;
  cursor: ew-resize;
  transition: transform 0.15s ease;
}
.curtain-knob:hover {
  transform: translate(-50%, -50%) scale(1.15);
  background: #232738;
}

.tag-badge {
  position: absolute;
  bottom: 14px;
  background: rgba(12, 14, 20, 0.88);
  backdrop-filter: blur(10px);
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 600;
  z-index: 20;
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  pointer-events: none;
}
.tag-badge.left { left: 14px; color: var(--text-sub); }
.tag-badge.right { right: 14px; color: var(--accent-emerald); }

/* FLOATING CANVAS HUD */
.canvas-hud {
  position: absolute;
  bottom: 18px;
  z-index: 30;
  background: rgba(16, 18, 26, 0.88);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-bright);
  padding: 4px 8px;
  border-radius: var(--radius-pill);
  display: flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.65);
}
.btn-hud {
  background: transparent;
  border: none;
  color: var(--text-sub);
  font-size: 11px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 5px;
}
.btn-hud:hover {
  background: var(--bg-input);
  color: #ffffff;
}
.btn-hud.active {
  background: var(--accent-primary);
  color: #ffffff;
}

/* EMPTY STATE VIEWPORT */
.empty-viewport {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
  gap: 14px;
}
.empty-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: rgba(82, 70, 234, 0.15);
  border: 1px solid rgba(82, 70, 234, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}
.empty-title {
  font-size: 17px;
  font-weight: 700;
  color: #ffffff;
}
.empty-subtitle {
  font-size: 12px;
  color: var(--text-sub);
  max-width: 400px;
  line-height: 1.5;
}
.empty-actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

/* SPINNER */
.viewport-loader {
  position: absolute;
  display: none;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  z-index: 40;
  background: rgba(12, 14, 20, 0.88);
  backdrop-filter: blur(12px);
  padding: 20px 30px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-bright);
}
.spinner-ring {
  width: 28px;
  height: 28px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* TIMELINE DECK */
.timeline-deck {
  height: 56px;
  padding: 0 20px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  display: flex;
  align-items: center;
  gap: 16px;
  z-index: 10;
}
.deck-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
}
.btn-deck {
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  color: var(--text-sub);
  width: 32px;
  height: 28px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.15s ease;
}
.btn-deck:hover {
  background: var(--bg-elevated);
  color: var(--text-main);
  border-color: var(--border-bright);
}

.scrubber-zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.scrubber-readout {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-sub);
  font-family: var(--font-mono);
}
.quick-jumps {
  display: flex;
  gap: 4px;
}
.jump-link {
  font-size: 10px;
  color: var(--text-dim);
  cursor: pointer;
  padding: 1px 6px;
  border-radius: 4px;
}
.jump-link:hover { color: var(--accent-cyan); background: var(--bg-input); }

.scrubber-track {
  width: 100%;
  height: 5px;
  -webkit-appearance: none;
  background: var(--bg-input);
  border-radius: var(--radius-pill);
  outline: none;
  cursor: pointer;
  margin: 0;
  padding: 0;
}
.scrubber-track::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  background: #ffffff;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 1px 6px rgba(0,0,0,0.6);
}

/* =========================================================================
   RIGHT SIDEBAR: STUDIO CONTROLS (LESS EDGY, MORE POLISHED)
   ========================================================================= */
.sidebar-panel {
  width: 440px;
  min-width: 440px;
  max-width: 440px;
  background: var(--bg-surface);
  border-left: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.studio-tabs {
  display: flex;
  background: var(--bg-app);
  border-bottom: 1px solid var(--border-subtle);
  padding: 4px 6px 0;
  gap: 2px;
}
.studio-tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-sub);
  font-size: 11px;
  font-weight: 600;
  padding: 10px 2px 8px;
  cursor: pointer;
  text-align: center;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}
.studio-tab-btn:hover { color: var(--text-main); }
.studio-tab-btn.active {
  color: #ffffff;
  border-bottom-color: var(--accent-primary);
}

.studio-scroll {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.studio-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.btn-reset-link {
  font-size: 11px;
  color: var(--accent-cyan);
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: 600;
}
.btn-reset-link:hover { text-decoration: underline; }

.media-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.meta-matrix {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.meta-box {
  background: var(--bg-input);
  border-radius: var(--radius-md);
  padding: 8px 10px;
}
.meta-box-label {
  font-size: 9px;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-bottom: 2px;
}
.meta-box-val {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
  font-family: var(--font-mono);
}

.action-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.btn-subtle {
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  color: var(--text-sub);
  padding: 7px 10px;
  border-radius: var(--radius-md);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s ease;
}
.btn-subtle:hover {
  background: var(--bg-elevated);
  color: var(--text-main);
  border-color: var(--border-bright);
}
.btn-subtle.highlight {
  border-color: rgba(82, 70, 234, 0.6);
  color: #c7d2fe;
}

/* QUICK LOOK PRESET CHIPS */

/* GLOBAL CUSTOM DARK SCROLLBAR - NO WHITE OS TRACKS */
* {
  scrollbar-width: thin;
  scrollbar-color: rgba(225, 29, 72, 0.3) transparent;
}
::-webkit-scrollbar {
  width: 4px !important;
  height: 4px !important;
}
::-webkit-scrollbar-track {
  background: transparent !important;
}
::-webkit-scrollbar-thumb {
  background: rgba(225, 29, 72, 0.25) !important;
  border-radius: 4px !important;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(225, 29, 72, 0.55) !important;
}

/* QUICK LOOK PRESET CHIPS - ZERO SCROLLBAR */
.quick-preset-bar {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 2px;
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
}
.quick-preset-bar::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  background: transparent !important;
}
.chip-preset {
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  color: var(--text-sub);
  font-size: 10px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}
.chip-preset:hover {
  background: var(--bg-elevated);
  color: #ffffff;
  border-color: var(--accent-primary);
}

/* ================= 3-WAY COLOR WHEELS (DAVINCI STYLE) ================= */
.color-wheels-container {
  display: flex;
  gap: 8px;
  justify-content: space-between;
  padding: 4px 0;
}
.wheel-unit {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}
.wheel-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
}
.wheel-disc-wrap {
  position: relative;
  width: 86px;
  height: 86px;
  border-radius: 50%;
  background: conic-gradient(red, yellow, lime, cyan, blue, magenta, red);
  padding: 2px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
}
.wheel-disc-inner {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(circle, #222534 0%, rgba(34,37,52,0.7) 65%, transparent 100%);
  cursor: crosshair;
}
.wheel-crosshair {
  position: absolute;
  top: 50%; left: 50%;
  width: 8px; height: 8px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.3);
  transform: translate(-50%, -50%);
  pointer-events: none;
}
.wheel-puck {
  position: absolute;
  top: 50%; left: 50%;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #000000;
  transform: translate(-50%, -50%);
  box-shadow: 0 1px 4px rgba(0,0,0,0.8);
  pointer-events: none;
}
.wheel-readout {
  font-size: 9px;
  font-family: var(--font-mono);
  color: var(--text-dim);
  display: flex;
  gap: 4px;
}
.wheel-slider-track {
  width: 86px;
  height: 4px;
  -webkit-appearance: none;
  background: var(--bg-input);
  border-radius: var(--radius-pill);
  outline: none;
  margin: 0;
}
.wheel-slider-track::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 10px; height: 10px;
  background: #ffffff;
  border-radius: 50%;
  cursor: pointer;
}

/* SLIDERS */
.slider-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.slider-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.slider-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-sub);
}
.slider-val {
  font-weight: 600;
  font-family: var(--font-mono);
  color: #ffffff;
}
.slider-bar {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  background: var(--bg-input);
  border-radius: var(--radius-pill);
  outline: none;
  cursor: pointer;
  margin: 0;
  padding: 0;
}
.slider-bar::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 13px;
  height: 13px;
  background: #ffffff;
  border-radius: 50%;
  cursor: pointer;
}

/* SEGMENTED SWITCH */
.segmented-bar {
  display: flex;
  background: var(--bg-input);
  padding: 3px;
  border-radius: var(--radius-md);
  gap: 2px;
}
.seg-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-sub);
  font-size: 11px;
  font-weight: 600;
  padding: 6px 3px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: center;
  transition: all 0.15s ease;
}
.seg-btn:hover { color: var(--text-main); }
.seg-btn.active {
  background: var(--bg-panel);
  color: #ffffff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.4);
}

/* TOGGLES */
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}
.toggle-label-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.toggle-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
}
.toggle-desc {
  font-size: 10px;
  color: var(--text-dim);
}
.toggle-switch {
  position: relative;
  width: 36px;
  height: 20px;
  cursor: pointer;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: var(--bg-input);
  border-radius: var(--radius-pill);
  transition: 0.2s;
}
.toggle-slider:before {
  position: absolute;
  content: "";
  height: 14px;
  width: 14px;
  left: 3px;
  bottom: 3px;
  background: #ffffff;
  border-radius: 50%;
  transition: 0.2s;
}
.toggle-switch input:checked + .toggle-slider { background: var(--accent-primary); }
.toggle-switch input:checked + .toggle-slider:before { transform: translateX(16px); }

/* BATCH QUEUE ITEMS */
.batch-queue-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 190px;
  overflow-y: auto;
}
.queue-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-input);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  font-size: 11px;
}
.queue-row input[type="checkbox"] { cursor: pointer; }
.queue-item-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-main);
}
.queue-status-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: var(--radius-pill);
  background: var(--bg-elevated);
  color: var(--text-dim);
}
.queue-status-badge.processing { background: #3b111c; color: #fecdd3; }
.queue-status-badge.done { background: #064e3b; color: #6ee7b7; }

/* SIDEBAR DOCK */
.sidebar-dock {
  padding: 14px 18px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.dock-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-sub);
}
.link-action {
  color: var(--accent-cyan);
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
}
.link-action:hover { text-decoration: underline; }

.export-progress-track {
  width: 100%;
  height: 6px;
  background: var(--bg-input);
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.export-progress-fill {
  width: 0%;
  height: 100%;
  background: linear-gradient(90deg, #e11d48, #38bdf8);
  border-radius: var(--radius-pill);
  transition: width 0.2s ease-out;
}

.btn-primary-export {
  width: 100%;
  background: var(--accent-primary);
  color: #ffffff;
  border: none;
  padding: 11px 0;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--ease-fluid);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-primary-export:hover {
  background: var(--accent-primary-hover);
  box-shadow: 0 4px 16px rgba(82, 70, 234, 0.4);
}
.btn-primary-export.cancel { background: var(--accent-rose); }

/* VISUAL AUDITION MODAL */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(16px);
  z-index: 1000;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.modal-window {
  background: var(--bg-panel);
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-lg);
  width: 920px;
  max-width: 95vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.8);
}
.modal-head {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal-title { font-size: 14px; font-weight: 700; color: #ffffff; }
.btn-close-modal { background: transparent; border: none; color: var(--text-dim); font-size: 18px; cursor: pointer; }
.btn-close-modal:hover { color: #ffffff; }

.modal-body {
  padding: 20px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.audition-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s var(--ease-fluid);
  display: flex;
  flex-direction: column;
}
.audition-card:hover {
  border-color: var(--accent-primary);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(82, 70, 234, 0.3);
}
.audition-thumb-wrap {
  width: 100%;
  height: 140px;
  background: #000000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.audition-thumb { width: 100%; height: 100%; object-fit: cover; }
.audition-info { padding: 10px 12px; display: flex; flex-direction: column; gap: 4px; }
.audition-name-row { display: flex; align-items: center; justify-content: space-between; }
.audition-name { font-weight: 600; font-size: 12px; color: #ffffff; }
.audition-tag { font-size: 9px; font-weight: 700; color: var(--accent-cyan); background: rgba(56, 189, 248, 0.15); padding: 1px 6px; border-radius: var(--radius-pill); text-transform: uppercase; }
.audition-desc { font-size: 11px; color: var(--text-sub); line-height: 1.3; }

/* TOAST */
.toast-msg {
  position: fixed;
  bottom: 24px;
  left: 24px;
  background: rgba(16, 18, 26, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-bright);
  padding: 10px 18px;
  border-radius: var(--radius-md);
  color: #ffffff;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
  z-index: 1000;
  transform: translateY(100px);
  opacity: 0;
  transition: all 0.3s var(--ease-fluid);
}
.toast-msg.show { transform: translateY(0); opacity: 1; }
</style>
</head>
<body>

<!-- SVG GPU FILTER DEFS FOR 60FPS REAL-TIME LIVE SHADING -->
<svg width="0" height="0" style="position:absolute; pointer-events:none;">
  <filter id="liveGrade">
    <feColorMatrix id="feGradeMatrix" type="matrix" values="
      1 0 0 0 0
      0 1 0 0 0
      0 0 1 0 0
      0 0 0 1 0" />
  </filter>
  <filter id="vhsChromaFilter" x="-10%" y="-10%" width="120%" height="120%">
    <!-- Authentic NTSC VHS Chroma Subcarrier Horizontal Smear & Delay -->
    <feColorMatrix type="matrix" values="
      1 0 0 0 0
      0 0 0 0 0
      0 0 0 0 0
      0 0 0 1 0" in="SourceGraphic" result="red"/>
    <feOffset id="vhsRedOffset" dx="-3.5" dy="0" in="red" result="red_shift"/>
    <feGaussianBlur stdDeviation="2.0 0" in="red_shift" result="red_smear"/>

    <feColorMatrix type="matrix" values="
      0 0 0 0 0
      0 1 0 0 0
      0 0 0 0 0
      0 0 0 1 0" in="SourceGraphic" result="green"/>

    <feColorMatrix type="matrix" values="
      0 0 0 0 0
      0 0 0 0 0
      0 0 1 0 0
      0 0 0 1 0" in="SourceGraphic" result="blue"/>
    <feOffset id="vhsBlueOffset" dx="3.5" dy="0" in="blue" result="blue_shift"/>
    <feGaussianBlur stdDeviation="2.5 0" in="blue_shift" result="blue_smear"/>

    <feBlend mode="screen" in="red_smear" in2="green" result="rg"/>
    <feBlend mode="screen" in="rg" in2="blue_smear" result="vhs_rgb"/>
    <feComponentTransfer in="vhs_rgb">
      <feFuncR type="linear" slope="1.06" intercept="0.015"/>
      <feFuncG type="linear" slope="1.00" intercept="0.01"/>
      <feFuncB type="linear" slope="0.94" intercept="0.02"/>
    </feComponentTransfer>
  </filter>
</svg>

<div class="app-shell">

  <!-- ================= LEFT: MAIN STAGE ================= -->
  <main class="stage-main">
    
    <!-- TOPBAR -->
    <header class="topbar">
      <div class="brand-group">
        <div class="brand-logo">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5">
            <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
            <polyline points="2 17 12 22 22 17"></polyline>
            <polyline points="2 12 12 17 22 12"></polyline>
          </svg>
        </div>
        <div class="brand-title" id="lblAppName">Apple Upscaler</div>
        <div class="brand-badge" id="lblAppEdition" style="background: rgba(225, 29, 72, 0.2); border: 1px solid rgba(225, 29, 72, 0.4); color: #fb7185;">Neural Pro</div>

        <!-- FOLDER VIDEO NAVIGATION & SWITCHER -->
        <div class="folder-nav-group" id="folderNavGroup" style="display:none;" title="Switch through videos in folder (Shortcuts: [ and ])">
          <button class="btn-nav-arrow" onclick="prevMedia()" title="Previous Video ([)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
          <select class="select-nav-media" id="selActiveMedia" onchange="selectMedia(parseInt(this.value))" title="Select active video"></select>
          <span class="lbl-nav-counter" id="lblNavCounter">1 / 1</span>
          <button class="btn-nav-arrow" onclick="nextMedia()" title="Next Video (])">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
      </div>

      <div class="topbar-actions">
        <!-- SUGGEST ENHANCEMENTS VISUAL AUDITION -->
        <button class="btn-action suggest" onclick="openAuditionModal()" title="See 6 AI remaster treatments on this frame">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path>
          </svg>
          Suggest Enhancements
        </button>

        <!-- 10-SECOND PREVIEW RENDER -->
        <button class="btn-action" onclick="renderQuickSample(10)" title="Fast 10s test render with active color grade">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          10s Test Render
        </button>

        <!-- WATCH IN POTPLAYER -->
        <button class="btn-action" id="btnPotPlayer" onclick="watchInPotPlayer()" title="Watch color-graded sample in PotPlayer with dual-audio & subtitles">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
          <span id="lblPotPlayerBtn">Watch Remastered</span>
        </button>

        <!-- SAVE / LOAD PRESET -->
        <button class="btn-action" onclick="saveCustomPreset()" title="Save current grading preset to file">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
            <polyline points="17 21 17 13 7 13 7 21"></polyline>
            <polyline points="7 3 7 8 15 8"></polyline>
          </svg>
          Save
        </button>
        <button class="btn-action" onclick="loadCustomPreset()" title="Load grading preset from file">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Load
        </button>
      </div>
    </header>

    <!-- VIEWPORT CINEMA -->
    <div class="viewport-area" id="viewportArea">
      
      <!-- MODE PILL -->
      <div class="viewmode-pill" id="viewModePill" style="display:none;">
        <button class="tab-pill active" id="tabSplit" onclick="setViewMode('split')">Split Curtain</button>
        <button class="tab-pill" id="tabOriginal" onclick="setViewMode('original')">Source</button>
        <button class="tab-pill" id="tabRemaster" onclick="setViewMode('remaster')">Remastered</button>
        <button class="tab-pill" id="tabABCompare" onclick="setViewMode('ab_compare')">A/B Scaler Compare</button>
      </div>

      <!-- LOADER -->
      <div class="viewport-loader" id="frameLoader">
        <div class="spinner-ring"></div>
        <span id="lblLoaderText" style="font-size: 12px; color: var(--text-sub);">Processing frame...</span>
      </div>

      <!-- CANVAS BOUNDS -->
      <div class="canvas-bounds" id="canvasBounds" style="display:none;">
        <img class="layer-before" id="imgBefore" style="display:none;" onload="this.style.display='block'; onFrameLoaded();" onerror="this.style.display='none';" />
        
        <div class="layer-after-clip" id="afterClip">
          <img class="layer-after" id="imgAfter" style="display:none;" onload="this.style.display='block';" onerror="this.style.display='none';" />
        </div>

        <!-- CRT & VHS OVERLAYS -->
        <div class="crt-overlay" id="crtOverlay"></div>
        <div class="vhs-tracking-band" id="vhsTrackingBand"></div>

        <div class="curtain-divider" id="curtainDivider">
          <div class="curtain-knob">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </div>
        </div>

        <div class="tag-badge left" id="tagSource">Source</div>
        <div class="tag-badge right" id="tagRemaster">Remastered</div>
      </div>

      <!-- FLOATING CANVAS HUD (ZOOM & DETAIL INSPECTION) -->
      <div class="canvas-hud" id="canvasHud" style="display:none;">
        <button class="btn-hud" id="btnZoomToggle" onclick="toggleZoomMode()">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="11" y1="8" x2="11" y2="14"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
          </svg>
          <span id="lblZoom">1:1 Zoom</span>
        </button>
        <button class="btn-hud" onclick="toggleFullscreen()" title="Fullscreen Viewport">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
          </svg>
        </button>
      </div>

      <!-- EMPTY STATE (NO MEDIA LOADED) -->
      <div class="empty-viewport" id="emptyViewport">
        <div class="empty-icon-wrap">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2">
            <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
            <polyline points="2 17 12 22 22 17"></polyline>
            <polyline points="2 12 12 17 22 12"></polyline>
          </svg>
        </div>
        <div class="empty-title">Ready for Remastering</div>
        <div class="empty-subtitle">Load any anime video or photo (MP4, MKV, AVI, WebM, PNG, JPG, TIFF) to begin neural upscaling, 3-way color grading, and CRT/VHS simulation.</div>
        <div class="empty-actions">
          <button class="btn-subtle highlight" onclick="triggerAddFiles()">Browse Files</button>
          <button class="btn-subtle" onclick="triggerAddFolder()">Batch Folder</button>
        </div>
      </div>

    </div>

    <!-- BOTTOM TIMELINE DECK -->
    <footer class="timeline-deck" id="timelineDeck">
      <div class="deck-buttons">
        <button class="btn-deck" onclick="stepTime(-10)" title="Step -10 seconds">-10s</button>
        <button class="btn-deck" onclick="stepTime(-1)" title="Step -1 second">-1s</button>
        <button class="btn-deck" onclick="refreshFrame()" title="Refresh frame">Sync</button>
        <button class="btn-deck" onclick="stepTime(1)" title="Step +1 second">+1s</button>
        <button class="btn-deck" onclick="stepTime(10)" title="Step +10 seconds">+10s</button>
      </div>

      <div class="scrubber-zone">
        <div class="scrubber-readout">
          <span id="lblTimeline">00:00:00 / 00:00:00</span>
          
          <div class="quick-jumps" id="quickJumps">
            <span class="jump-link" onclick="jumpPercent(0.10)">10%</span>
            <span class="jump-link" onclick="jumpPercent(0.25)">25%</span>
            <span class="jump-link" onclick="jumpPercent(0.50)">50%</span>
            <span class="jump-link" onclick="jumpPercent(0.75)">75%</span>
          </div>

          <span id="lblFrameTech">Ready</span>
        </div>
        <input type="range" class="scrubber-track" id="timelineScrubber" min="0" max="100" value="0"
               oninput="onScrubInput(this.value)" onchange="onScrubCommit(this.value)">
      </div>
    </footer>

  </main>

  <!-- ================= RIGHT: STUDIO SIDEBAR ================= -->
  <aside class="sidebar-panel">
    
    <!-- TABS -->
    <nav class="studio-tabs">
      <button class="studio-tab-btn active" onclick="switchSidebarTab('tabColor', this)">Color & Wheels</button>
      <button class="studio-tab-btn" onclick="switchSidebarTab('tabRetroCRT', this)">Retro CRT/VHS</button>
      <button class="studio-tab-btn" onclick="switchSidebarTab('tabAIUpscale', this)">AI Upscaling</button>
      <button class="studio-tab-btn" onclick="switchSidebarTab('tabRestoration', this)">Cel Polish</button>
      <button class="studio-tab-btn" onclick="switchSidebarTab('tabGeometry', this)">Geometry</button>
      <button class="studio-tab-btn" onclick="switchSidebarTab('tabBatch', this)">Batch Queue</button>
      <button class="studio-tab-btn" onclick="switchSidebarTab('tabExport', this)">Export</button>
    </nav>

    <!-- TAB 1: COLOR & WHEELS -->
    <div class="studio-scroll" id="tabColor">
      
      <!-- Media Header -->
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title" id="lblMediaTypeBadge">Active Media</span>
          <span id="lblFileSize" style="font-size: 11px; color: var(--text-dim); font-family: var(--font-mono);">-- MB</span>
        </div>
        <div class="media-name" id="lblVideoName">No media loaded</div>
        
        <div class="meta-matrix">
          <div class="meta-box">
            <div class="meta-box-label">Resolution & Aspect</div>
            <div class="meta-box-val" id="valMetaRes">--</div>
          </div>
          <div class="meta-box">
            <div class="meta-box-label">Codec & Frame Rate</div>
            <div class="meta-box-val" id="valMetaCodec">--</div>
          </div>
        </div>

        <div class="action-grid-2">
          <button class="btn-subtle" onclick="triggerAddFiles()">+ Add Files</button>
          <button class="btn-subtle" onclick="triggerAddFolder()">+ Add Folder</button>
        </div>
      </div>

      <!-- ONE-CLICK QUICK PRESETS -->
      <div class="studio-card">
        <div class="card-title">Color Grading Profiles</div>
        <div class="quick-preset-bar">
          <button class="chip-preset" onclick="quickApplyPreset('cel_master')">Apple Master</button>
          <button class="chip-preset" onclick="quickApplyPreset('film_35mm')">35mm Film</button>
          <button class="chip-preset" onclick="quickApplyPreset('ink_sharp')">Ink 4K</button>
          <button class="chip-preset" onclick="quickApplyPreset('hdr_pop')">HDR Pop</button>
          <button class="chip-preset" onclick="quickApplyPreset('retro_crt')">90s CRT</button>
          <button class="chip-preset" onclick="quickApplyPreset('oled_clean')">OLED Clean</button>
        </div>
      </div>

      <!-- AI COLOR MATCHING -->
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">AI Color Matching</span>
          <span style="font-size: 10px; color: var(--accent-cyan); font-weight: 600;">Reinhard Neural Transfer</span>
        </div>
        <div style="font-size: 11px; color: var(--text-sub); line-height: 1.3;">
          Recreate the color grading of any reference screenshot or film frame automatically.
        </div>
        <button class="btn-subtle highlight" onclick="triggerColorMatch()" style="width: 100%;">
          Match Color from Reference Image...
        </button>
      </div>

      <!-- 3-WAY COLOR WHEELS (DAVINCI STYLE) -->
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">Lift / Gamma / Gain Color Wheels</span>
          <button class="btn-reset-link" onclick="resetColorWheels()">Reset Wheels</button>
        </div>

        <div class="color-wheels-container">
          <!-- LIFT WHEEL -->
          <div class="wheel-unit">
            <div class="wheel-title">Lift (Shadows)</div>
            <div class="wheel-disc-wrap">
              <div class="wheel-disc-inner" id="wheelLift" onmousedown="startWheelDrag(event, 'lift')" ondblclick="resetSingleWheel('lift')">
                <div class="wheel-crosshair"></div>
                <div class="wheel-puck" id="puckLift"></div>
              </div>
            </div>
            <div class="wheel-readout" id="lblLiftReadout">R0 G0 B0</div>
            <input type="range" class="wheel-slider-track" id="slLiftMaster" min="-0.2" max="0.2" step="0.01" value="0"
                   oninput="onWheelMasterLive('lift', this.value)" title="Lift Master Level">
          </div>

          <!-- GAMMA WHEEL -->
          <div class="wheel-unit">
            <div class="wheel-title">Gamma (Midtones)</div>
            <div class="wheel-disc-wrap">
              <div class="wheel-disc-inner" id="wheelGamma" onmousedown="startWheelDrag(event, 'gamma')" ondblclick="resetSingleWheel('gamma')">
                <div class="wheel-crosshair"></div>
                <div class="wheel-puck" id="puckGamma"></div>
              </div>
            </div>
            <div class="wheel-readout" id="lblGammaReadout">R0 G0 B0</div>
            <input type="range" class="wheel-slider-track" id="slGammaMaster" min="-0.2" max="0.2" step="0.01" value="0"
                   oninput="onWheelMasterLive('gamma', this.value)" title="Gamma Master Level">
          </div>

          <!-- GAIN WHEEL -->
          <div class="wheel-unit">
            <div class="wheel-title">Gain (Highlights)</div>
            <div class="wheel-disc-wrap">
              <div class="wheel-disc-inner" id="wheelGain" onmousedown="startWheelDrag(event, 'gain')" ondblclick="resetSingleWheel('gain')">
                <div class="wheel-crosshair"></div>
                <div class="wheel-puck" id="puckGain"></div>
              </div>
            </div>
            <div class="wheel-readout" id="lblGainReadout">R0 G0 B0</div>
            <input type="range" class="wheel-slider-track" id="slGainMaster" min="-0.2" max="0.2" step="0.01" value="0"
                   oninput="onWheelMasterLive('gain', this.value)" title="Gain Master Level">
          </div>
        </div>
      </div>

      <!-- PRIMARY COLOR SLIDERS -->
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">Primary Color Grading</span>
          <button class="btn-reset-link" onclick="resetSlidersToDefault()">Reset Defaults</button>
        </div>
        
        <div class="slider-group">
          
          <div class="slider-row">
            <div class="slider-meta">
              <span>Exposure Compensation</span>
              <span class="slider-val" id="valExposure">0.0 EV</span>
            </div>
            <input type="range" class="slider-bar" id="slExposure" min="-1.5" max="1.5" step="0.05" value="0.0"
                   oninput="onParamChangeLive('exposure', this.value, 'valExposure')">
          </div>

          <div class="slider-row">
            <div class="slider-meta">
              <span>Dynamic Contrast</span>
              <span class="slider-val" id="valContrast">1.14</span>
            </div>
            <input type="range" class="slider-bar" id="slContrast" min="0.70" max="1.60" step="0.02" value="1.14"
                   oninput="onParamChangeLive('contrast', this.value, 'valContrast')">
          </div>

          <div class="slider-row">
            <div class="slider-meta">
              <span>Color Saturation</span>
              <span class="slider-val" id="valSaturation">1.26</span>
            </div>
            <input type="range" class="slider-bar" id="slSaturation" min="0.50" max="1.80" step="0.02" value="1.26"
                   oninput="onParamChangeLive('saturation', this.value, 'valSaturation')">
          </div>

          <div class="slider-row">
            <div class="slider-meta">
              <span>Shadow De-Fog (Gamma Curve)</span>
              <span class="slider-val" id="valGamma">0.88</span>
            </div>
            <input type="range" class="slider-bar" id="slGamma" min="0.60" max="1.20" step="0.02" value="0.88"
                   oninput="onParamChangeLive('gamma', this.value, 'valGamma')">
          </div>

          <div class="slider-row">
            <div class="slider-meta">
              <span>Black Pedestal Floor</span>
              <span class="slider-val" id="valBrightness">-0.018</span>
            </div>
            <input type="range" class="slider-bar" id="slBrightness" min="-0.08" max="0.06" step="0.002" value="-0.018"
                   oninput="onParamChangeLive('brightness', this.value, 'valBrightness')">
          </div>

          <div class="slider-row">
            <div class="slider-meta">
              <span>Color Temperature</span>
              <span class="slider-val" id="valTemp">0</span>
            </div>
            <input type="range" class="slider-bar" id="slTemp" min="-30" max="30" step="1" value="0"
                   oninput="onParamChangeLive('temp', this.value, 'valTemp')">
          </div>

          <div class="slider-row">
            <div class="slider-meta">
              <span>AMD CAS Line Sharpening</span>
              <span class="slider-val" id="valSharpness">0.80</span>
            </div>
            <input type="range" class="slider-bar" id="slSharpness" min="0" max="1" step="0.02" value="0.80"
                   oninput="onParamChangeLive('sharpness', this.value, 'valSharpness')">
          </div>

        </div>
      </div>

      <!-- 3D LUT PROFILE -->
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">3D LUT Profile (.cube)</span>
          <button class="btn-subtle" onclick="triggerBrowseLUT()">Load .cube...</button>
        </div>

        <div class="segmented-bar">
          <button class="seg-btn active" onclick="setLutMode('none', this)">None</button>
          <button class="seg-btn" onclick="setLutMode('cel_master', this)">Cel Master</button>
          <button class="seg-btn" onclick="setLutMode('cinema_35mm', this)">Cinema 35mm</button>
          <button class="seg-btn" id="btnCustomLut" onclick="setLutMode('custom', this)" style="display:none;">Custom</button>
        </div>

        <div class="slider-row" id="rowLutIntensity">
          <div class="slider-meta">
            <span>LUT Intensity Blend</span>
            <span class="slider-val" id="valLutIntensity">100%</span>
          </div>
          <input type="range" class="slider-bar" id="slLutIntensity" min="0.1" max="1.0" step="0.05" value="1.0"
                 oninput="onParamChangeLive('lut_intensity', this.value, 'valLutIntensity')">
        </div>
      </div>

    </div>

    <!-- TAB 2: RETRO CRT & VHS SIMULATION (NEW FEATURE) -->
    <div class="studio-scroll" id="tabRetroCRT" style="display:none;">
      
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">CRT Television Simulation</span>
          <span style="font-size: 10px; color: var(--accent-amber); font-weight: 700;">ANALOG TUBE HARDWARE</span>
        </div>
        <div style="font-size: 11px; color: var(--text-sub); line-height: 1.4;">
          Authentic vintage CRT television simulation with aperture grille scanlines and curved glass bloom.
        </div>

        <div class="toggle-row">
          <div class="toggle-label-wrap">
            <div class="toggle-title">Aperture Grille Scanlines</div>
            <div class="toggle-desc">Horizontal phosphor scanline simulation</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkCrtScanlines" onchange="onToggleCRTScanlines(this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="slider-row">
          <div class="slider-meta">
            <span>Scanline Intensity</span>
            <span class="slider-val" id="valCrtIntensity">35%</span>
          </div>
          <input type="range" class="slider-bar" id="slCrtIntensity" min="0.1" max="0.8" step="0.05" value="0.35"
                 oninput="onCrtIntensityChange(this.value)">
        </div>

        <div class="toggle-row">
          <div class="toggle-label-wrap">
            <div class="toggle-title">Curved Glass Screen (Tube Curvature)</div>
            <div class="toggle-desc">Authentic spherical barrel distortion of retro monitors</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkCrtCurve" onchange="onToggleCRTCurve(this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">VHS Tape Analog Emulation</span>
          <span style="font-size: 10px; color: var(--accent-rose); font-weight: 700;">TAPE ARTIFACTS</span>
        </div>

        <div class="toggle-row">
          <div class="toggle-label-wrap">
            <div class="toggle-title">VHS Tape Analog Mode</div>
            <div class="toggle-desc">Prism RGB color fringing and analog tape tracking</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkVhsMode" onchange="onToggleVHSMode(this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="slider-row">
          <div class="slider-meta">
            <span>Chromatic Aberration (Prism Fringe)</span>
            <span class="slider-val" id="valVhsChroma">2.0 px</span>
          </div>
          <input type="range" class="slider-bar" id="slVhsChroma" min="1.0" max="6.0" step="0.5" value="2.0"
                 oninput="onVhsChromaChange(this.value)">
        </div>
      </div>

      <div class="studio-card">
        <div class="card-title">Retro Audio Dialogue Presence</div>
        <div class="toggle-row">
          <div class="toggle-label-wrap">
            <div class="toggle-title">Dialogue Clarity & Tape Hiss Cleanup</div>
            <div class="toggle-desc">Cleans vintage analog tape hiss and elevates dialogue frequencies</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkAudioEQ" onchange="onToggleAudioEQ(this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

    </div>

    <!-- TAB 3: AI UPSCALING (REAL-ESRGAN & A/B COMPARE) -->
    <div class="studio-scroll" id="tabAIUpscale" style="display:none;">
      
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">AI Neural Detail Reconstruction</span>
          <span style="font-size: 10px; color: var(--accent-emerald); font-weight: 700;">RTX VULKAN ACCELERATED</span>
        </div>
        <div style="font-size: 11px; color: var(--text-sub); line-height: 1.4;">
          Unlike traditional interpolation (Lanczos), Real-ESRGAN neural networks synthesize and reconstruct missing line-art and texture details.
        </div>

        <div style="font-size: 10px; color: var(--text-dim); text-transform: uppercase; font-weight: 700; margin-top: 4px;">Upscaling Engine</div>
        <div class="segmented-bar" style="flex-direction: column; gap: 4px; background: transparent; padding: 0;">
          <button class="seg-btn active" style="text-align: left; padding: 8px 12px; border-radius: 8px; background: var(--bg-input);" onclick="setAIModel('realesr-animevideov3', this)">
            <div style="font-weight: 700; color: #ffffff;">Real-ESRGAN Anime V3 (Neural Reconstruction)</div>
            <div style="font-size: 10px; color: var(--text-sub);">Neural detail reconstruction trained specifically for anime line art</div>
          </button>
          <button class="seg-btn" style="text-align: left; padding: 8px 12px; border-radius: 8px; background: var(--bg-input);" onclick="setAIModel('realesrgan-x4plus-anime', this)">
            <div style="font-weight: 700; color: #ffffff;">Real-ESRGAN 6B Anime Cel (Max Redraw)</div>
            <div style="font-size: 10px; color: var(--text-sub);">Deep convolutional neural model for vintage 480p/576p cels</div>
          </button>
          <button class="seg-btn" style="text-align: left; padding: 8px 12px; border-radius: 8px; background: var(--bg-input);" onclick="setAIModel('lanczos', this)">
            <div style="font-weight: 700; color: #ffffff;">Lanczos-3 Sinc (150+ FPS Fast Scaler)</div>
            <div style="font-size: 10px; color: var(--text-sub);">Ultra-fast mathematical interpolation + AMD CAS sharpening</div>
          </button>
          <button class="seg-btn" style="text-align: left; padding: 8px 12px; border-radius: 8px; background: var(--bg-input);" onclick="setAIModel('spline36', this)">
            <div style="font-weight: 700; color: #ffffff;">Spline36 (Crisp Outlines)</div>
            <div style="font-size: 10px; color: var(--text-sub);">Mathematical spline curve outline preservation</div>
          </button>
        </div>
      </div>

      <!-- AUTO SCENE DETECTION -->
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">Auto Scene Detection</span>
          <button class="btn-subtle" onclick="triggerDetectScenes()">Detect Cut Points</button>
        </div>
        <div style="font-size: 11px; color: var(--text-sub); line-height: 1.3;">
          Detects scene changes automatically and indexes cut points for fast timeline navigation.
        </div>
        <div id="sceneListStrip" style="display: flex; flex-wrap: wrap; gap: 4px; max-height: 120px; overflow-y: auto;">
          <div style="font-size: 11px; color: var(--text-dim);">Click 'Detect Cut Points' to index scene cuts</div>
        </div>
      </div>

    </div>

    <!-- TAB 4: CEL RESTORATION & LINE ART -->
    <div class="studio-scroll" id="tabRestoration" style="display:none;">
      
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">Ink Density & Cel Deflicker</span>
          <span style="font-size: 10px; color: var(--accent-cyan); font-weight: 700;">PRO CEL TOOLS</span>
        </div>

        <div class="slider-row">
          <div class="slider-meta">
            <span>Line Art Darkener (Ink Infill)</span>
            <span class="slider-val" id="valLineDarken">0.00</span>
          </div>
          <input type="range" class="slider-bar" id="slLineDarken" min="0" max="1" step="0.05" value="0.00"
                 oninput="onParamChangeLive('line_darken', this.value, 'valLineDarken')">
        </div>

        <div class="toggle-row">
          <div class="toggle-label-wrap">
            <div class="toggle-title">Temporal Cel Deflicker</div>
            <div class="toggle-desc">Eliminates uneven physical lighting exposure flicker across static cels</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkCelDeflicker" onchange="onToggleParam('cel_deflicker', this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

      <div class="studio-card">
        <div class="card-title">AI Denoise & Film Grain</div>
        
        <div class="slider-row">
          <div class="slider-meta">
            <span>Cel Animation Denoise (HQDN3D)</span>
            <span class="slider-val" id="valDenoise">3.0</span>
          </div>
          <input type="range" class="slider-bar" id="slDenoise" min="0" max="8" step="0.5" value="3.0"
                 oninput="onParamChangeLive('denoise', this.value, 'valDenoise')">
        </div>

        <div class="slider-row">
          <div class="slider-meta">
            <span>Organic 35mm Film Grain</span>
            <span class="slider-val" id="valGrain">0.00</span>
          </div>
          <input type="range" class="slider-bar" id="slGrain" min="0" max="0.25" step="0.01" value="0.00"
                 oninput="onParamChangeLive('grain', this.value, 'valGrain')">
        </div>

        <div class="toggle-row">
          <div class="toggle-label-wrap">
            <div class="toggle-title">16-Bit Deband Dithering</div>
            <div class="toggle-desc">Removes color banding in gradients and skies</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkDeband" checked onchange="onToggleParam('deband', this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

      <div class="studio-card">
        <div class="card-title">Artifact & Interlacing Correction</div>

        <div class="toggle-row">
          <div class="toggle-label-wrap">
            <div class="toggle-title">Clean Dirty Overscan Borders</div>
            <div class="toggle-desc">Crops 2px noisy analog borders</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkEdgeClean" checked onchange="onToggleParam('edge_clean', this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="toggle-row">
          <div class="toggle-label-wrap">
            <div class="toggle-title">Hardware De-interlacing (YADIF)</div>
            <div class="toggle-desc">Removes combed interlaced lines for 480i/576i sources</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkDeinterlace" onchange="onToggleParam('deinterlace', this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

    </div>

    <!-- TAB 5: GEOMETRY & FRAMING -->
    <div class="studio-scroll" id="tabGeometry" style="display:none;">
      
      <div class="studio-card">
        <div class="card-title">Aspect Ratio & Canvas Framing</div>
        <div class="segmented-bar">
          <button class="seg-btn active" onclick="setFraming('4:3 Pillarbox', this)">4:3 Pillarbox</button>
          <button class="seg-btn" onclick="setFraming('16:9 Ambient', this)">16:9 Ambient Wings</button>
          <button class="seg-btn" onclick="setFraming('16:9 Crop', this)">16:9 Fill</button>
        </div>
      </div>

      <div class="studio-card">
        <div class="card-title">Output Target Resolution</div>
        <div class="segmented-bar">
          <button class="seg-btn" onclick="setResolution('Match Source', this)">Source</button>
          <button class="seg-btn" onclick="setResolution('720p', this)">720p</button>
          <button class="seg-btn active" onclick="setResolution('1080p', this)">1080p</button>
          <button class="seg-btn" onclick="setResolution('2K', this)">2K</button>
          <button class="seg-btn" onclick="setResolution('4K', this)">4K</button>
          <button class="seg-btn" onclick="setResolution('8K', this)">8K</button>
        </div>
      </div>

    </div>

    <!-- TAB 6: BATCH PROCESSING QUEUE -->
    <div class="studio-scroll" id="tabBatch" style="display:none;">
      
      <div class="studio-card">
        <div class="card-head">
          <span class="card-title">Season Batch Queue</span>
          <div style="display: flex; gap: 4px;">
            <button class="btn-subtle" onclick="selectAllBatch(true)">All</button>
            <button class="btn-subtle" onclick="selectAllBatch(false)">None</button>
          </div>
        </div>
        <div style="font-size: 11px; color: var(--text-sub);">
          Batch process multiple episodes or entire seasons sequentially without manual intervention.
        </div>
        
        <div class="batch-queue-list" id="batchQueueList">
          <div style="color: var(--text-dim); font-size: 11px;">No videos in queue</div>
        </div>
      </div>

    </div>

    <!-- TAB 7: EXPORT -->
    <div class="studio-scroll" id="tabExport" style="display:none;">
      
      <div class="studio-card" id="cardTrimControls">
        <div class="card-title">Scene In / Out Trimming</div>
        <div class="action-grid-2">
          <button class="btn-subtle" onclick="markInPoint()">Mark In Point [</button>
          <button class="btn-subtle" onclick="markOutPoint()">Mark Out Point ]</button>
        </div>
        <div class="meta-matrix">
          <div class="meta-box">
            <div class="meta-box-label">START TIME (IN)</div>
            <div class="meta-box-val" id="valTrimIn">00:00:00</div>
          </div>
          <div class="meta-box">
            <div class="meta-box-label">END TIME (OUT)</div>
            <div class="meta-box-val" id="valTrimOut">Full Video</div>
          </div>
        </div>
        <button class="btn-subtle" onclick="resetTrim()" style="width: 100%;">Reset to Full Video</button>
      </div>

      <div class="studio-card">
        <div class="card-title">Export Container & Encoder</div>
        
        <div style="font-size: 10px; color: var(--text-dim); text-transform: uppercase; font-weight: 700; margin-bottom: 2px;">Container Format</div>
        <div class="segmented-bar">
          <button class="seg-btn active" onclick="setExportFormat('mkv', this)">MKV</button>
          <button class="seg-btn" onclick="setExportFormat('mp4', this)">MP4</button>
          <button class="seg-btn" onclick="setExportFormat('mov', this)">MOV</button>
          <button class="seg-btn" onclick="setExportFormat('webm', this)">WebM</button>
        </div>

        <div style="font-size: 10px; color: var(--text-dim); text-transform: uppercase; font-weight: 700; margin-top: 6px; margin-bottom: 2px;">Hardware Encoder</div>
        <div class="segmented-bar">
          <button class="seg-btn active" onclick="setGpuMode('nvenc_hevc', this)">RTX HEVC</button>
          <button class="seg-btn" onclick="setGpuMode('nvenc_h264', this)">NVENC H.264</button>
          <button class="seg-btn" onclick="setGpuMode('av1', this)">AV1 NVENC</button>
          <button class="seg-btn" onclick="setGpuMode('cpu', this)">CPU x265</button>
        </div>

        <div class="slider-row">
          <div class="slider-meta">
            <span>Constant Quality (CQ)</span>
            <span class="slider-val" id="valCQ">20 (Master)</span>
          </div>
          <input type="range" class="slider-bar" id="slCQ" min="15" max="28" step="1" value="20"
                 oninput="onParamChangeLive('cq', this.value, 'valCQ')">
        </div>

        <div class="toggle-row" style="margin-top: 6px; padding-top: 8px; border-top: 1px solid var(--border-subtle);">
          <div class="toggle-label-wrap">
            <div class="toggle-title" style="color: var(--accent-rose);">Delete Original File After Successful Export</div>
            <div class="toggle-desc">Automatically removes source file once export is 100% verified</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="chkDeleteOriginal" onchange="onToggleDeleteOriginal(this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

    </div>

    <!-- SIDEBAR FOOTER DOCK -->
    <div class="sidebar-dock">
      <div class="dock-meta-row">
        <span>Destination: <span id="lblOutDirName" style="color: var(--text-main);">Remastered_Studio_Output</span></span>
        <span class="link-action" onclick="openOutputDir()">Open Folder</span>
      </div>

      <div class="dock-meta-row" style="font-family: var(--font-mono);">
        <span id="telSpeed">Speed: -- fps</span>
        <span id="telEta">ETA: --:--</span>
      </div>

      <div class="export-progress-track">
        <div class="export-progress-fill" id="exportProgFill"></div>
      </div>

      <button class="btn-primary-export" id="btnExportVideo" onclick="toggleExport()">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span id="lblExportBtn">Export Remastered Media</span>
      </button>
    </div>

  </aside>

</div>

<!-- VISUAL AUDITION MODAL -->
<div class="modal-overlay" id="auditionModal">
  <div class="modal-window">
    <div class="modal-head">
      <div>
        <div class="modal-title">AI Profile Recommender - Visual Audition</div>
        <div style="font-size: 11px; color: var(--text-sub);">Select a treatment based on visual comparison of this active frame</div>
      </div>
      <button class="btn-close-modal" onclick="closeAuditionModal()">&times;</button>
    </div>
    
    <div class="modal-body" id="auditionGrid">
      <div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; height: 260px; color: var(--text-sub); gap: 12px;">
        <div class="spinner-ring"></div>
        <span>Rendering 6 AI remaster treatments...</span>
      </div>
    </div>
  </div>
</div>

<!-- TOAST -->
<div class="toast-msg" id="toastMsg">
  <span id="toastText">Ready</span>
</div>

<script>
// =========================================================================
// APPLICATION STATE
// =========================================================================
let state = {
  queue: [],
  activeIndex: -1,
  currentSec: 0,
  curtainPct: 50,
  settings: {
    contrast: 1.140,
    gamma: 0.880,
    saturation: 1.260,
    sharpness: 0.800,
    brightness: -0.018,
    exposure: 0.0,
    temp: 0.0,
    tint: 0.0,
    denoise: 3.0,
    grain: 0.0,
    deband: true,
    edge_clean: true,
    deinterlace: false,
    resolution: "1080p",
    framing: "4:3 Pillarbox",
    audio_mode: "copy",
    sub_mode: "copy",
    export_fmt: "mkv",
    photo_fmt: "png",
    gpu: "nvenc_hevc",
    cq: 20,
    trim_enabled: false,
    trim_in: "00:00:00",
    trim_out: "00:00:00",
    lut_mode: "none",
    lut_intensity: 1.0,
    ai_model: "realesr-animevideov3",
    delete_original: false,
    lift_r: 0.0, lift_g: 0.0, lift_b: 0.0, lift_master: 0.0,
    gamma_r: 0.0, gamma_g: 0.0, gamma_b: 0.0, gamma_master: 0.0,
    gain_r: 0.0, gain_g: 0.0, gain_b: 0.0, gain_master: 0.0,
    crt_scanlines: false,
    crt_intensity: 0.35,
    crt_curve: false,
    vhs_mode: false,
    vhs_chroma: 2.0,
    line_darken: 0.0,
    cel_deflicker: false,
    audio_eq: false
  },
  viewMode: 'split',
  isEncoding: false,
  debounceTimer: null,
  activeWheel: null,
  isCurtainDragging: false,
  isZoomed: false,
  auditionCards: []
};

// =========================================================================
// INITIALIZATION (DUAL HOOK TO PREVENT WEBVIEW READY RACE CONDITION)
// =========================================================================
async function startApp() {
  try {
    let init = await window.pywebview.api.get_initial_state();
    state.queue = init.queue || [];
    state.activeIndex = init.active_index;
    
    if (init.branding) {
      if (init.branding.app_name) document.getElementById('lblAppName').innerText = init.branding.app_name;
      if (init.branding.app_edition) document.getElementById('lblAppEdition').innerText = init.branding.app_edition;
    }

    setupCurtainDivider();
    setupKeyboardShortcuts();
    updateBatchQueueUI();
    updateFolderNav();

    if (state.activeIndex >= 0 && state.queue.length > 0) {
      await selectMedia(state.activeIndex);
    } else {
      let loader = document.getElementById('frameLoader');
      if (loader) loader.style.display = 'none';
      document.getElementById('emptyViewport').style.display = 'flex';
      document.getElementById('canvasBounds').style.display = 'none';
      document.getElementById('viewModePill').style.display = 'none';
      document.getElementById('canvasHud').style.display = 'none';
      document.getElementById('folderNavGroup').style.display = 'none';
    }
  } catch (err) {
    console.error("Initialization error:", err);
    let loader = document.getElementById('frameLoader');
    if (loader) loader.style.display = 'none';
  }
}

if (window.pywebview && window.pywebview.api) {
  startApp();
} else {
  window.addEventListener('pywebviewready', startApp);
}

function showToast(msg) {
  let t = document.getElementById('toastMsg');
  document.getElementById('toastText').innerText = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3500);
}

// =========================================================================
// FOLDER NAVIGATION (SWITCH VIDEOS IN ACTIVE FOLDER)
// =========================================================================
function updateFolderNav() {
  let group = document.getElementById('folderNavGroup');
  let counter = document.getElementById('lblNavCounter');
  let sel = document.getElementById('selActiveMedia');
  if (state.queue && state.queue.length > 0) {
    if (group) group.style.display = 'flex';
    if (counter) counter.innerText = `${state.activeIndex + 1} / ${state.queue.length}`;
    if (sel) {
      sel.innerHTML = state.queue.map((item, idx) => `
        <option value="${idx}" ${idx === state.activeIndex ? 'selected' : ''}>${idx + 1}. ${item.filename || item.name}</option>
      `).join('');
    }
  } else {
    if (group) group.style.display = 'none';
  }
}

let historyUndoStack = [];
let historyRedoStack = [];

function pushHistory(desc) {
  historyUndoStack.push({
    desc: desc,
    settings: JSON.parse(JSON.stringify(state.settings))
  });
  if (historyUndoStack.length > 50) historyUndoStack.shift();
  historyRedoStack = [];
}

function undo() {
  if (historyUndoStack.length === 0) {
    showToast("Nothing to undo");
    return;
  }
  historyRedoStack.push({
    desc: "Redo",
    settings: JSON.parse(JSON.stringify(state.settings))
  });
  const prev = historyUndoStack.pop();
  for (let k in prev.settings) state.settings[k] = prev.settings[k];
  syncAllInputsFromSettings();
  updateLiveGPUGrade();
  refreshFrame();
  showToast(`↩️ Undid: ${prev.desc}`);
}

function redo() {
  if (historyRedoStack.length === 0) {
    showToast("Nothing to redo");
    return;
  }
  historyUndoStack.push({
    desc: "Undo",
    settings: JSON.parse(JSON.stringify(state.settings))
  });
  const nxt = historyRedoStack.pop();
  for (let k in nxt.settings) state.settings[k] = nxt.settings[k];
  syncAllInputsFromSettings();
  updateLiveGPUGrade();
  refreshFrame();
  showToast(`↪️ Redid: ${nxt.desc}`);
}

function syncAllInputsFromSettings() {
  const s = state.settings;
  const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
  const setText = (id, t) => { const el = document.getElementById(id); if (el) el.innerText = t; };

  setVal('slContrast', s.contrast);
  setText('valContrast', s.contrast.toFixed(2));
  setVal('slBrightness', s.brightness);
  setText('valBrightness', s.brightness.toFixed(3));
  setVal('slGamma', s.gamma);
  setText('valGamma', s.gamma.toFixed(2));
  setVal('slSaturation', s.saturation);
  setText('valSaturation', s.saturation.toFixed(2));
  setVal('slExposure', s.exposure);
  setText('valExposure', `${s.exposure > 0 ? '+' : ''}${s.exposure.toFixed(1)} EV`);
  setVal('slTemp', s.temp);
  setText('valTemp', s.temp);
  setVal('slTint', s.tint);
  setText('valTint', s.tint);
  setVal('slDenoise', s.denoise);
  setText('valDenoise', s.denoise.toFixed(1));
  setVal('slSharpness', s.sharpness);
  setText('valSharpness', s.sharpness.toFixed(2));

  if (document.getElementById('chkCrtScanlines')) {
    document.getElementById('chkCrtScanlines').checked = !!s.crt_scanlines;
    const crt = document.getElementById('crtOverlay');
    if (crt) crt.style.display = s.crt_scanlines ? 'block' : 'none';
  }
  if (document.getElementById('chkCrtCurve')) {
    document.getElementById('chkCrtCurve').checked = !!s.crt_curve;
    const b = document.getElementById('canvasBounds');
    if (b) {
      if (s.crt_curve) b.classList.add('crt-curved');
      else b.classList.remove('crt-curved');
    }
  }
  if (document.getElementById('chkVhsMode')) {
    document.getElementById('chkVhsMode').checked = !!s.vhs_mode;
    const band = document.getElementById('vhsTrackingBand');
    if (band) band.style.display = s.vhs_mode ? 'block' : 'none';
  }
}

async function prevMedia() {
  if (state.queue.length <= 1) {
    showToast("Single media in active queue");
    return;
  }
  let nextIdx = state.activeIndex - 1;
  if (nextIdx < 0) nextIdx = state.queue.length - 1;
  await selectMedia(nextIdx);
  showToast(`Switched: ${state.queue[nextIdx].filename}`);
}

async function nextMedia() {
  if (state.queue.length <= 1) {
    showToast("Single media in active queue");
    return;
  }
  let nextIdx = (state.activeIndex + 1) % state.queue.length;
  await selectMedia(nextIdx);
  showToast(`Switched: ${state.queue[nextIdx].filename}`);
}

function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    // Shortcuts for Undo & Redo (Ctrl+Z and Ctrl+Y / Ctrl+Shift+Z)
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
      e.preventDefault();
      undo();
      return;
    }
    if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'y' || (e.key.toLowerCase() === 'z' && e.shiftKey))) {
      e.preventDefault();
      redo();
      return;
    }

    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === '[' || (e.altKey && e.key === 'ArrowLeft')) {
      prevMedia();
    } else if (e.key === ']' || (e.altKey && e.key === 'ArrowRight')) {
      nextMedia();
    } else if (e.key === 'f' || e.key === 'F11') {
      toggleFullscreen();
    }
  });
}

async function selectMedia(idx) {
  if (idx < 0 || !state.queue || idx >= state.queue.length) return;
  state.activeIndex = idx;
  try {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.select_queue_item(idx);
    }
  } catch (e) {
    console.error("select_queue_item error:", e);
  }
  let item = state.queue[idx];
  if (!item) return;

  document.getElementById('emptyViewport').style.display = 'none';
  document.getElementById('canvasBounds').style.display = 'inline-flex';
  document.getElementById('viewModePill').style.display = 'flex';
  document.getElementById('canvasHud').style.display = 'flex';

  document.getElementById('lblVideoName').innerText = item.filename || item.name;
  document.getElementById('lblFileSize').innerText = `${item.size_mb} MB`;
  document.getElementById('lblMediaTypeBadge').innerText = item.is_image ? 'Active Photo' : 'Active Video';
  document.getElementById('valMetaRes').innerText = `${item.width}x${item.height} (${item.dar || '16:9'})`;
  document.getElementById('valMetaCodec').innerText = `${(item.video_codec || 'unknown').toUpperCase()} / ${item.fps} fps`;

  updateFolderNav();
  updateResolutionTags();

  let scrubber = document.getElementById('timelineScrubber');
  let jumps = document.getElementById('quickJumps');
  let trimCard = document.getElementById('cardTrimControls');

  if (item.is_image) {
    if (scrubber) scrubber.style.display = 'none';
    if (jumps) jumps.style.display = 'none';
    if (trimCard) trimCard.style.display = 'none';
    document.getElementById('lblTimeline').innerText = 'Photo Mode - Single Frame Canvas';
    document.getElementById('lblExportBtn').innerText = 'Export Remastered Photo';
    state.currentSec = 0;
  } else {
    if (scrubber) scrubber.style.display = 'block';
    if (jumps) jumps.style.display = 'flex';
    if (trimCard) trimCard.style.display = 'flex';
    document.getElementById('lblExportBtn').innerText = 'Export Remastered Media';
    
    let dur = Math.max(1, Math.floor(item.duration));
    if (scrubber) {
      scrubber.min = 0;
      scrubber.max = dur;
      let defSec = dur > 60 ? Math.floor(Math.min(dur * 0.1, 45)) : Math.floor(dur / 4);
      scrubber.value = defSec;
      state.currentSec = defSec;
    }
    updateTimeReadout();
  }

  updateBatchQueueUI();
  await refreshFrame();
}

function updateResolutionTags() {
  let item = state.queue[state.activeIndex];
  if (!item) return;
  document.getElementById('tabOriginal').innerText = `Source (${item.height}p)`;
  document.getElementById('tabRemaster').innerText = `Remastered (${state.settings.resolution})`;
  document.getElementById('tagSource').innerText = `Source (${item.height}p)`;
  document.getElementById('tagRemaster').innerText = `Remastered (${state.settings.resolution})`;
}

function formatSec(s) {
  s = Math.floor(s || 0);
  let h = Math.floor(s / 3600);
  let m = Math.floor((s % 3600) / 60);
  let sec = s % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
  return `${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
}

function updateTimeReadout() {
  let dur = state.queue[state.activeIndex]?.duration || 0;
  document.getElementById('lblTimeline').innerText = `${formatSec(state.currentSec)} / ${formatSec(dur)}`;
}

function onScrubInput(val) {
  state.currentSec = parseInt(val);
  updateTimeReadout();
}

function onScrubCommit(val) {
  state.currentSec = parseInt(val);
  refreshFrame();
}

function jumpPercent(pct) {
  let dur = state.queue[state.activeIndex]?.duration || 0;
  if (dur <= 0) return;
  state.currentSec = Math.floor(dur * pct);
  document.getElementById('timelineScrubber').value = state.currentSec;
  updateTimeReadout();
  refreshFrame();
}

function stepTime(delta) {
  let dur = state.queue[state.activeIndex]?.duration || 0;
  state.currentSec = Math.max(0, Math.min(dur, state.currentSec + delta));
  document.getElementById('timelineScrubber').value = state.currentSec;
  updateTimeReadout();
  refreshFrame();
}

// =========================================================================
// REAL-TIME 60FPS GPU VIEWPORT SHADING (ZERO LAG DURING DRAGGING)
// =========================================================================
function updateLiveGPUGrade() {
  const imgAfter = document.getElementById('imgAfter');
  if (!imgAfter) return;

  const s = state.settings;
  const expMult = Math.pow(2, s.exposure);
  const brightPct = Math.round((1.0 + (s.brightness * 1.5)) * expMult * 100);
  const contPct = Math.round(s.contrast * 100);
  const satPct = Math.round(s.saturation * 100);

  const matrix = document.getElementById('feGradeMatrix');
  if (matrix) {
    let r_gain = (1.0 + s.gain_r + s.gain_master);
    let g_gain = (1.0 + s.gain_g + s.gain_master);
    let b_gain = (1.0 + s.gain_b + s.gain_master);

    let r_off = (s.lift_r + s.lift_master + (s.temp * 0.004));
    let g_off = (s.lift_g + s.lift_master - (s.tint * 0.004));
    let b_off = (s.lift_b + s.lift_master - (s.temp * 0.004));

    matrix.setAttribute('values', `
      ${r_gain.toFixed(3)} 0 0 0 ${r_off.toFixed(3)}
      0 ${g_gain.toFixed(3)} 0 0 ${g_off.toFixed(3)}
      0 0 ${b_gain.toFixed(3)} 0 ${b_off.toFixed(3)}
      0 0 0 1 0
    `.trim());
  }

  let filterStr = `contrast(${contPct}%) saturate(${satPct}%) brightness(${brightPct}%) url(#liveGrade)`;
  if (s.vhs_mode) {
    let ch = s.vhs_chroma || 2.5;
    const rOff = document.getElementById('vhsRedOffset');
    const bOff = document.getElementById('vhsBlueOffset');
    if (rOff) rOff.setAttribute('dx', (-ch * 1.2).toFixed(1));
    if (bOff) bOff.setAttribute('dx', (ch * 1.2).toFixed(1));
    filterStr += ` url(#vhsChromaFilter)`;
  }
  imgAfter.style.filter = filterStr;
}

// =========================================================================
// RETRO CRT & VHS SIMULATION (INTERACTIVE GPU TOGGLES)
// =========================================================================
function onToggleCRTScanlines(checked) {
  state.settings.crt_scanlines = checked;
  const overlay = document.getElementById('crtOverlay');
  overlay.style.display = checked ? 'block' : 'none';
  showToast(checked ? "CRT Scanlines enabled" : "CRT Scanlines disabled");
}

function onCrtIntensityChange(val) {
  val = parseFloat(val);
  state.settings.crt_intensity = val;
  document.getElementById('valCrtIntensity').innerText = `${Math.round(val * 100)}%`;
  const overlay = document.getElementById('crtOverlay');
  overlay.style.opacity = (val * 1.5).toString();
}

function onToggleCRTCurve(checked) {
  state.settings.crt_curve = checked;
  const bounds = document.getElementById('canvasBounds');
  if (checked) bounds.classList.add('crt-curved');
  else bounds.classList.remove('crt-curved');
  showToast(checked ? "Curved glass tube monitor enabled" : "Flat canvas enabled");
}

function onToggleVHSMode(checked) {
  state.settings.vhs_mode = checked;
  const imgAfter = document.getElementById('imgAfter');
  const clip = document.getElementById('afterClip');
  const band = document.getElementById('vhsTrackingBand');
  
  if (band) band.style.display = checked ? 'block' : 'none';
  if (imgAfter) {
    if (checked) imgAfter.classList.add('vhs-jitter');
    else imgAfter.classList.remove('vhs-jitter');
  }
  if (clip) {
    if (checked) clip.style.filter = 'url(#vhsChromaFilter)';
    else clip.style.filter = 'none';
  }
  updateLiveGPUGrade();
  showToast(checked ? "NTSC VHS Analog Tape Mode active" : "VHS Mode disabled");
}

function onVhsChromaChange(val) {
  val = parseFloat(val);
  state.settings.vhs_chroma = val;
  const lbl = document.getElementById('valVhsChroma');
  if (lbl) lbl.innerText = `${val.toFixed(1)} px`;
  const rOff = document.getElementById('vhsRedOffset');
  const bOff = document.getElementById('vhsBlueOffset');
  if (rOff) rOff.setAttribute('dx', (-val).toFixed(1));
  if (bOff) bOff.setAttribute('dx', val.toFixed(1));
}

function onToggleCRTScanlines(checked) {
  state.settings.crt_scanlines = checked;
  const overlay = document.getElementById('crtOverlay');
  if (overlay) overlay.style.display = checked ? 'block' : 'none';
  showToast(checked ? "Trinitron CRT Phosphor Triads enabled" : "CRT scanlines disabled");
}

function onCrtIntensityChange(val) {
  val = parseFloat(val);
  state.settings.crt_intensity = val;
  const lbl = document.getElementById('valCrtIntensity');
  if (lbl) lbl.innerText = `${Math.round(val * 100)}%`;
  const overlay = document.getElementById('crtOverlay');
  if (overlay) overlay.style.opacity = (val * 1.5).toString();
}

function onToggleCRTCurve(checked) {
  state.settings.crt_curve = checked;
  const bounds = document.getElementById('canvasBounds');
  if (bounds) {
    if (checked) bounds.classList.add('crt-curved');
    else bounds.classList.remove('crt-curved');
  }
  showToast(checked ? "Curved glass tube monitor enabled" : "Flat canvas enabled");
}

function onToggleAudioEQ(checked) {
  state.settings.audio_eq = checked;
  showToast(checked ? "Audio dialogue presence & hiss filter enabled" : "Audio filter disabled");
}

// =========================================================================
// FRAME RENDERING (HIGH-PRECISION BACKGROUND SYNC)
// =========================================================================
async function refreshFrame() {
  if (state.activeIndex < 0) return;
  
  let loader = document.getElementById('frameLoader');
  if (loader) {
    loader.style.display = 'flex';
    document.getElementById('lblLoaderText').innerText = `Processing frame...`;
  }

  try {
    if (state.viewMode === 'ab_compare') {
      let res = await window.pywebview.api.get_ab_model_comparison(state.currentSec, state.settings);
      if (res && res.model_a && res.model_b) {
        let imgB = document.getElementById('imgBefore');
        let imgA = document.getElementById('imgAfter');
        imgB.src = res.model_b;
        imgA.src = res.model_a;
        imgB.style.display = 'block';
        imgA.style.display = 'block';
        imgB.style.opacity = '1';
        imgA.style.opacity = '1';
        document.getElementById('tagSource').innerText = res.name_b;
        document.getElementById('tagRemaster').innerText = res.name_a;
        document.getElementById('lblFrameTech').innerText = "A/B Neural vs Traditional Scaler Compare";
        document.getElementById('canvasBounds').style.display = 'inline-flex';
        document.getElementById('curtainDivider').style.display = 'block';
        document.getElementById('tagSource').style.display = 'block';
        document.getElementById('tagRemaster').style.display = 'block';
      }
      return;
    }

    let res = await window.pywebview.api.extract_preview_frames(state.currentSec, state.settings);
    if (res && res.before && res.after) {
      let imgB = document.getElementById('imgBefore');
      let imgA = document.getElementById('imgAfter');
      imgB.src = res.before;
      imgA.src = res.after;
      imgB.style.display = 'block';
      imgA.style.display = 'block';
      imgB.style.opacity = '1';
      imgA.style.opacity = '1';
      document.getElementById('canvasBounds').style.display = 'inline-flex';
      
      let isSplit = (state.viewMode === 'split');
      let isRemaster = (state.viewMode === 'remaster');
      let isOriginal = (state.viewMode === 'original');

      const afterClip = document.getElementById('afterClip');
      const divider = document.getElementById('curtainDivider');
      const tagL = document.getElementById('tagSource');
      const tagR = document.getElementById('tagRemaster');

      if (isSplit) {
        afterClip.style.display = 'block';
        afterClip.style.clipPath = `inset(0 0 0 ${state.curtainPct || 50}%)`;
        divider.style.display = 'block';
        tagL.style.display = 'block';
        tagR.style.display = 'block';
      } else if (isRemaster) {
        afterClip.style.display = 'block';
        afterClip.style.clipPath = 'inset(0 0 0 0%)';
        divider.style.display = 'none';
        tagL.style.display = 'none';
        tagR.style.display = 'block';
      } else if (isOriginal) {
        afterClip.style.display = 'none';
        divider.style.display = 'none';
        tagL.style.display = 'block';
        tagR.style.display = 'none';
      }

      let modelTag = state.settings.ai_model.includes('realesr') ? 'Real-ESRGAN AI' : 'Lanczos-3 + CAS';
      document.getElementById('lblFrameTech').innerText = `${res.width}x${res.height} ${modelTag} (${res.timestamp})`;
      updateResolutionTags();
    }
  } catch (err) {
    console.error("refreshFrame error:", err);
  } finally {
    if (loader) loader.style.display = 'none';
  }
}

function onFrameLoaded() {
  let loader = document.getElementById('frameLoader');
  let imgB = document.getElementById('imgBefore');
  let imgA = document.getElementById('imgAfter');
  let div = document.getElementById('curtainDivider');
  let tagL = document.getElementById('tagSource');
  let tagR = document.getElementById('tagRemaster');

  loader.style.display = 'none';
  imgB.style.opacity = '1';
  imgA.style.opacity = '1';

  if (state.viewMode === 'split' || state.viewMode === 'ab_compare') {
    div.style.display = 'block';
  }
  tagL.style.display = 'block';
  tagR.style.display = 'block';
}

// =========================================================================
// 100% FLUSH CURTAIN DIVIDER (0% TO 100% EDGE TO EDGE)
// =========================================================================
function setCurtainPos(pct) {
  pct = Math.max(0, Math.min(100, pct));
  state.curtainPct = pct;
  const divider = document.getElementById('curtainDivider');
  const afterClip = document.getElementById('afterClip');

  if (divider) divider.style.left = `${pct}%`;
  if (afterClip) afterClip.style.clipPath = `inset(0 0 0 ${pct}%)`;

  // Auto-fade badges if curtain handle approaches them to prevent overlapping/clipping
  const tagL = document.getElementById('tagSource');
  const tagR = document.getElementById('tagRemaster');
  if (tagL) {
    if (pct < 18) {
      tagL.style.opacity = '0';
      tagL.style.transform = 'translateY(6px)';
    } else {
      tagL.style.opacity = '1';
      tagL.style.transform = 'translateY(0)';
    }
  }
  if (tagR) {
    if (pct > 82) {
      tagR.style.opacity = '0';
      tagR.style.transform = 'translateY(6px)';
    } else {
      tagR.style.opacity = '1';
      tagR.style.transform = 'translateY(0)';
    }
  }
}

function setupCurtainDivider() {
  const bounds = document.getElementById('canvasBounds');

  const updateFromEvent = (e) => {
    const rect = bounds.getBoundingClientRect();
    if (rect.width <= 0) return;
    let x = e.clientX - rect.left;
    let pct = (x / rect.width) * 100;
    setCurtainPos(pct);
  };

  bounds.addEventListener('mousedown', (e) => {
    if (state.viewMode !== 'split' && state.viewMode !== 'ab_compare') return;
    state.isCurtainDragging = true;
    updateFromEvent(e);
  });

  window.addEventListener('mousemove', (e) => {
    if (!state.isCurtainDragging) return;
    updateFromEvent(e);
  });

  window.addEventListener('mouseup', () => {
    state.isCurtainDragging = false;
  });
}

async function setViewMode(mode) {
  let prevMode = state.viewMode;
  state.viewMode = mode;
  document.querySelectorAll('.tab-pill').forEach(t => t.classList.remove('active'));
  const afterClip = document.getElementById('afterClip');
  const divider = document.getElementById('curtainDivider');
  const loader = document.getElementById('frameLoader');
  const bounds = document.getElementById('canvasBounds');
  const tagL = document.getElementById('tagSource');
  const tagR = document.getElementById('tagRemaster');

  if (bounds) bounds.style.display = 'inline-flex';
  if (loader) loader.style.display = 'none';

  if (mode === 'split') {
    document.getElementById('tabSplit').classList.add('active');
    afterClip.style.display = 'block';
    setCurtainPos(state.curtainPct || 50);
    divider.style.display = 'block';
    tagL.style.display = 'block';
    tagR.style.display = 'block';
    updateResolutionTags();
    if (prevMode === 'ab_compare') {
      await refreshFrame();
    }
  } else if (mode === 'ab_compare') {
    document.getElementById('tabABCompare').classList.add('active');
    afterClip.style.display = 'block';
    setCurtainPos(state.curtainPct || 50);
    divider.style.display = 'block';
    tagL.style.display = 'block';
    tagR.style.display = 'block';
    await refreshFrame();
  } else if (mode === 'original') {
    document.getElementById('tabOriginal').classList.add('active');
    afterClip.style.display = 'none';
    divider.style.display = 'none';
    tagL.style.display = 'block';
    tagR.style.display = 'none';
    if (prevMode === 'ab_compare') {
      await refreshFrame();
    }
  } else if (mode === 'remaster') {
    document.getElementById('tabRemaster').classList.add('active');
    afterClip.style.display = 'block';
    afterClip.style.clipPath = 'inset(0 0 0 0%)';
    divider.style.display = 'none';
    tagL.style.display = 'none';
    tagR.style.display = 'block';
    if (prevMode === 'ab_compare') {
      await refreshFrame();
    }
  }
}

function toggleZoomMode() {
  state.isZoomed = !state.isZoomed;
  const bounds = document.getElementById('canvasBounds');
  const btn = document.getElementById('btnZoomToggle');
  if (state.isZoomed) {
    bounds.classList.add('zoom-100');
    btn.classList.add('active');
    document.getElementById('lblZoom').innerText = 'Fit Canvas';
    showToast("1:1 Pixel Zoom enabled (inspect neural sharpness)");
  } else {
    bounds.classList.remove('zoom-100');
    btn.classList.remove('active');
    document.getElementById('lblZoom').innerText = '1:1 Zoom';
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  } else {
    document.exitFullscreen().catch(() => {});
  }
}

// =========================================================================
// 3-WAY COLOR WHEELS (ZERO LAG REAL-TIME 60FPS)
// =========================================================================
function startWheelDrag(e, wheelType) {
  e.preventDefault();
  state.activeWheel = wheelType;
  updateWheelPosition(e, wheelType);

  const onMouseMove = (ev) => {
    if (state.activeWheel) {
      updateWheelPosition(ev, state.activeWheel);
      updateLiveGPUGrade();
    }
  };
  const onMouseUp = () => {
    state.activeWheel = null;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
    
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(() => {
      refreshFrame();
    }, 120);
  };
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
}

function updateWheelPosition(e, type) {
  const wheel = document.getElementById(`wheel${type.charAt(0).toUpperCase() + type.slice(1)}`);
  const rect = wheel.getBoundingClientRect();
  const radius = rect.width / 2;
  const cx = rect.left + radius;
  const cy = rect.top + radius;

  let dx = e.clientX - cx;
  let dy = e.clientY - cy;
  let dist = Math.sqrt(dx * dx + dy * dy);

  if (dist > radius - 6) {
    dx = (dx / dist) * (radius - 6);
    dy = (dy / dist) * (radius - 6);
  }

  const puck = document.getElementById(`puck${type.charAt(0).toUpperCase() + type.slice(1)}`);
  puck.style.left = `${radius + dx}px`;
  puck.style.top = `${radius + dy}px`;

  let angle = Math.atan2(dy, dx);
  let mag = Math.min(1.0, dist / radius) * 0.35;

  let r = Math.cos(angle) * mag;
  let g = Math.cos(angle - (2 * Math.PI / 3)) * mag;
  let b = Math.cos(angle + (2 * Math.PI / 3)) * mag;

  state.settings[`${type}_r`] = roundVal(r);
  state.settings[`${type}_g`] = roundVal(g);
  state.settings[`${type}_b`] = roundVal(b);

  const badge = document.getElementById(`lbl${type.charAt(0).toUpperCase() + type.slice(1)}Readout`);
  if (badge) {
    badge.innerText = `R${r >= 0 ? '+' : ''}${Math.round(r*100)} G${g >= 0 ? '+' : ''}${Math.round(g*100)} B${b >= 0 ? '+' : ''}${Math.round(b*100)}`;
  }
}

function onWheelMasterLive(type, val) {
  val = parseFloat(val);
  state.settings[`${type}_master`] = val;
  updateLiveGPUGrade();
  
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => {
    refreshFrame();
  }, 120);
}

function resetSingleWheel(type) {
  state.settings[`${type}_r`] = 0.0;
  state.settings[`${type}_g`] = 0.0;
  state.settings[`${type}_b`] = 0.0;
  state.settings[`${type}_master`] = 0.0;
  const puck = document.getElementById(`puck${type.charAt(0).toUpperCase() + type.slice(1)}`);
  puck.style.left = '50%';
  puck.style.top = '50%';
  document.getElementById(`sl${type.charAt(0).toUpperCase() + type.slice(1)}Master`).value = 0;
  const badge = document.getElementById(`lbl${type.charAt(0).toUpperCase() + type.slice(1)}Readout`);
  if (badge) badge.innerText = "R0 G0 B0";
  updateLiveGPUGrade();
  refreshFrame();
}

function resetColorWheels() {
  ['lift', 'gamma', 'gain'].forEach(t => resetSingleWheel(t));
  showToast("Reset 3-way color wheels to neutral");
}

function roundVal(v) { return Math.round(v * 1000) / 1000; }

// =========================================================================
// SLIDER LIVE 60FPS INTERACTION
// =========================================================================
function onParamChangeLive(key, val, lblId) {
  val = parseFloat(val);
  state.settings[key] = val;
  
  if (lblId) {
    if (key === 'exposure') document.getElementById(lblId).innerText = `${val >= 0 ? '+' : ''}${val.toFixed(2)} EV`;
    else if (key === 'temp' || key === 'tint') document.getElementById(lblId).innerText = `${val > 0 ? '+' : ''}${val}`;
    else if (key === 'lut_intensity') document.getElementById(lblId).innerText = `${Math.round(val * 100)}%`;
    else if (key === 'cq') document.getElementById(lblId).innerText = `${val} (${val <= 18 ? 'Master' : 'High Quality'})`;
    else if (key === 'line_darken') document.getElementById(lblId).innerText = val.toFixed(2);
    else document.getElementById(lblId).innerText = val.toFixed(key === 'brightness' ? 3 : 2);
  }

  updateLiveGPUGrade();

  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => {
    refreshFrame();
  }, 120);
}

function onToggleParam(key, checked) {
  state.settings[key] = checked;
  refreshFrame();
}

// =========================================================================
// QUICK PRESETS
// =========================================================================
function quickApplyPreset(presetId) {
  let presets = {
    cel_master: {"contrast": 1.140, "brightness": -0.018, "gamma": 0.880, "saturation": 1.260, "sharpness": 0.80, "denoise": 3.0, "temp": 0, "exposure": 0.0, "crt_scanlines": false, "vhs_mode": false},
    film_35mm: {"contrast": 1.080, "brightness": -0.010, "gamma": 0.940, "saturation": 1.120, "sharpness": 0.50, "denoise": 1.5, "temp": 14, "exposure": 0.0, "crt_scanlines": false, "vhs_mode": false},
    ink_sharp: {"contrast": 1.180, "brightness": -0.020, "gamma": 0.860, "saturation": 1.220, "sharpness": 1.00, "denoise": 4.5, "temp": 0, "exposure": 0.0, "crt_scanlines": false, "vhs_mode": false},
    hdr_pop: {"contrast": 1.250, "brightness": -0.028, "gamma": 0.840, "saturation": 1.380, "sharpness": 0.85, "denoise": 2.5, "temp": 0, "exposure": 0.1, "crt_scanlines": false, "vhs_mode": false},
    retro_crt: {"contrast": 1.120, "brightness": 0.005, "gamma": 0.900, "saturation": 1.320, "sharpness": 0.60, "denoise": 2.0, "temp": 8, "exposure": 0.0, "crt_scanlines": true, "vhs_mode": false},
    oled_clean: {"contrast": 1.160, "brightness": -0.015, "gamma": 0.880, "saturation": 1.180, "sharpness": 0.80, "denoise": 3.5, "temp": -10, "exposure": 0.0, "crt_scanlines": false, "vhs_mode": false}
  };

  let p = presets[presetId];
  if (!p) return;
  for (let k in p) state.settings[k] = p[k];

  document.getElementById('slContrast').value = p.contrast;
  document.getElementById('valContrast').innerText = p.contrast.toFixed(2);
  document.getElementById('slSaturation').value = p.saturation;
  document.getElementById('valSaturation').innerText = p.saturation.toFixed(2);
  document.getElementById('slGamma').value = p.gamma;
  document.getElementById('valGamma').innerText = p.gamma.toFixed(2);
  document.getElementById('slBrightness').value = p.brightness;
  document.getElementById('valBrightness').innerText = p.brightness.toFixed(3);
  document.getElementById('slSharpness').value = p.sharpness;
  document.getElementById('valSharpness').innerText = p.sharpness.toFixed(2);
  document.getElementById('slTemp').value = p.temp;
  document.getElementById('valTemp').innerText = `${p.temp > 0 ? '+' : ''}${p.temp}`;
  document.getElementById('slExposure').value = p.exposure;
  document.getElementById('valExposure').innerText = `${p.exposure.toFixed(2)} EV`;

  if (p.crt_scanlines !== undefined) {
    document.getElementById('chkCrtScanlines').checked = p.crt_scanlines;
    onToggleCRTScanlines(p.crt_scanlines);
  }

  updateLiveGPUGrade();
  showToast(`Applied: ${presetId.toUpperCase()}`);
  refreshFrame();
}

// =========================================================================
// AI COLOR MATCHING
// =========================================================================
async function triggerColorMatch() {
  showToast("Select a reference image to transfer color grading...");
  let res = await window.pywebview.api.match_color_from_reference_dialog(state.currentSec);
  if (res && res.success) {
    state.settings.contrast = res.contrast;
    state.settings.brightness = res.brightness;
    state.settings.saturation = res.saturation;
    state.settings.gain_r = res.gain_r;
    state.settings.gain_g = res.gain_g;
    state.settings.gain_b = res.gain_b;
    state.settings.lift_r = res.lift_r;
    state.settings.lift_g = res.lift_g;
    state.settings.lift_b = res.lift_b;

    document.getElementById('slContrast').value = res.contrast;
    document.getElementById('valContrast').innerText = res.contrast.toFixed(2);
    document.getElementById('slBrightness').value = res.brightness;
    document.getElementById('valBrightness').innerText = res.brightness.toFixed(3);
    document.getElementById('slSaturation').value = res.saturation;
    document.getElementById('valSaturation').innerText = res.saturation.toFixed(2);

    updateLiveGPUGrade();
    showToast(`Color matched to '${res.ref_name}'!`);
    refreshFrame();
  }
}

// =========================================================================
// CUSTOM PRESET SAVE / LOAD
// =========================================================================
async function saveCustomPreset() {
  let jsonStr = JSON.stringify(state.settings, null, 2);
  let fname = await window.pywebview.api.save_preset_dialog(jsonStr);
  if (fname) {
    showToast(`Saved preset '${fname}'!`);
  }
}

async function loadCustomPreset() {
  let res = await window.pywebview.api.load_preset_dialog();
  if (res && res.success && res.settings) {
    applyAuditionProfile(res.settings, res.name);
    showToast(`Loaded preset '${res.name}'!`);
  }
}

// =========================================================================
// AUTO SCENE DETECTION
// =========================================================================
async function triggerDetectScenes() {
  let strip = document.getElementById('sceneListStrip');
  strip.innerHTML = '<div style="font-size:11px; color:var(--accent-cyan); display:flex; gap:6px; align-items:center;"><div class="spinner-ring" style="width:14px;height:14px;border-width:2px;"></div> Indexing scene cuts...</div>';
  
  let scenes = await window.pywebview.api.detect_scenes_fast();
  if (scenes && scenes.length) {
    strip.innerHTML = scenes.map(s => `
      <button class="btn-subtle" style="padding:4px 8px; font-size:10px;" onclick="seekToScene(${s.seconds})">
        ${s.name} (${s.timestamp})
      </button>
    `).join('');
    showToast(`Detected ${scenes.length} scene cuts`);
  } else {
    strip.innerHTML = '<div style="font-size:11px; color:var(--text-dim);">No significant scene cuts found</div>';
  }
}

function seekToScene(sec) {
  state.currentSec = sec;
  document.getElementById('timelineScrubber').value = sec;
  updateTimeReadout();
  refreshFrame();
}

// =========================================================================
// BATCH QUEUE
// =========================================================================
function updateBatchQueueUI() {
  let list = document.getElementById('batchQueueList');
  if (!list) return;
  if (!state.queue || !state.queue.length) {
    list.innerHTML = '<div style="color:var(--text-dim); font-size:11px; padding:8px 0;">No media in queue</div>';
    return;
  }
  list.innerHTML = state.queue.map((item, idx) => `
    <div class="queue-row ${idx === state.activeIndex ? 'active' : ''}" style="${idx === state.activeIndex ? 'border-left: 2px solid var(--accent-primary); background: rgba(225, 29, 72, 0.12);' : ''}">
      <input type="checkbox" ${item.selected_for_batch !== false ? 'checked' : ''} onchange="onItemBatchToggle(${idx}, this.checked)" />
      <span class="queue-item-title" onclick="selectMedia(${idx})" style="cursor:pointer; ${idx === state.activeIndex ? 'color: #ffffff; font-weight: 600;' : ''}" title="${item.filename || item.name}">${idx + 1}. ${item.filename || item.name}</span>
      <span class="queue-status-badge ${item.status.toLowerCase()}">${item.status}</span>
    </div>
  `).join('');
}

async function onItemBatchToggle(idx, checked) {
  state.queue[idx].selected_for_batch = checked;
  await window.pywebview.api.toggle_queue_item_batch(idx, checked);
}

async function selectAllBatch(val) {
  state.queue = await window.pywebview.api.select_all_batch(val);
  updateBatchQueueUI();
}

// =========================================================================
// SIDEBAR TABS & PARAMETERS
// =========================================================================
function switchSidebarTab(tabId, btn) {
  document.querySelectorAll('.studio-tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.studio-scroll').forEach(p => p.style.display = 'none');
  btn.classList.add('active');
  document.getElementById(tabId).style.display = 'flex';
}

function setAIModel(model, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => {
    b.classList.remove('active');
    b.style.borderColor = 'transparent';
  });
  btn.classList.add('active');
  btn.style.borderColor = 'var(--accent-primary)';
  state.settings.ai_model = model;
  showToast(`Active Scaler: ${model}`);
  refreshFrame();
}

function setFraming(mode, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.framing = mode;
  refreshFrame();
}

function setResolution(res, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.resolution = res;
  updateResolutionTags();
  refreshFrame();
}

function setLutMode(mode, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.lut_mode = mode;
  refreshFrame();
}

async function triggerBrowseLUT() {
  let fname = await window.pywebview.api.browse_lut_dialog();
  if (fname) {
    let btnCustom = document.getElementById('btnCustomLut');
    btnCustom.style.display = 'block';
    btnCustom.innerText = fname.length > 12 ? fname.substring(0, 10) + '...' : fname;
    setLutMode('custom', btnCustom);
    showToast(`Loaded 3D LUT: ${fname}`);
  }
}

function setExportFormat(fmt, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.export_fmt = fmt;
}

function setGpuMode(mode, btn) {
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.settings.gpu = mode;
}

function onToggleDeleteOriginal(checked) {
  state.settings.delete_original = checked;
  if (checked) {
    showToast("Warning: Original source file will be deleted after export successfully finishes.");
  }
}

function resetSlidersToDefault() {
  let defs = {
    contrast: 1.140, brightness: -0.018, gamma: 0.880, saturation: 1.260, sharpness: 0.800,
    exposure: 0.0, temp: 0, tint: 0, denoise: 3.0, grain: 0.0, deband: true, edge_clean: true,
    deinterlace: false, lut_mode: "none", lut_intensity: 1.0, crt_scanlines: false, vhs_mode: false,
    line_darken: 0.0, cel_deflicker: false, audio_eq: false
  };
  for (let k in defs) state.settings[k] = defs[k];

  document.getElementById('slExposure').value = 0.0;
  document.getElementById('valExposure').innerText = "0.0 EV";
  document.getElementById('slContrast').value = 1.14;
  document.getElementById('valContrast').innerText = "1.14";
  document.getElementById('slSaturation').value = 1.26;
  document.getElementById('valSaturation').innerText = "1.26";
  document.getElementById('slGamma').value = 0.88;
  document.getElementById('valGamma').innerText = "0.88";
  document.getElementById('slBrightness').value = -0.018;
  document.getElementById('valBrightness').innerText = "-0.018";
  document.getElementById('slTemp').value = 0;
  document.getElementById('valTemp').innerText = "0";
  document.getElementById('slSharpness').value = 0.80;
  document.getElementById('valSharpness').innerText = "0.80";
  document.getElementById('slDenoise').value = 3.0;
  document.getElementById('valDenoise').innerText = "3.0";
  document.getElementById('slGrain').value = 0.0;
  document.getElementById('valGrain').innerText = "0.00";
  document.getElementById('slLineDarken').value = 0.0;
  document.getElementById('valLineDarken').innerText = "0.00";
  document.getElementById('chkCrtScanlines').checked = false;
  document.getElementById('chkCrtCurve').checked = false;
  document.getElementById('chkVhsMode').checked = false;
  document.getElementById('chkCelDeflicker').checked = false;
  document.getElementById('chkAudioEQ').checked = false;

  onToggleCRTScanlines(false);
  onToggleCRTCurve(false);
  onToggleVHSMode(false);
  resetColorWheels();
  updateLiveGPUGrade();
  showToast("Restored all sliders to calibrated defaults");
  refreshFrame();
}

// =========================================================================
// VISUAL AUDITION MODAL (SUGGEST ENHANCEMENTS - BUG FIXED)
// =========================================================================
async function openAuditionModal() {
  if (state.activeIndex < 0) {
    showToast("Load a video or photo first.");
    return;
  }
  let modal = document.getElementById('auditionModal');
  let grid = document.getElementById('auditionGrid');
  modal.style.display = 'flex';
  
  grid.innerHTML = `
    <div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; height: 260px; color: var(--text-sub); gap: 12px;">
      <div class="spinner-ring"></div>
      <span>Rendering 6 AI remaster treatments...</span>
    </div>
  `;

  let cards = await window.pywebview.api.get_preset_auditions(state.currentSec);
  state.auditionCards = cards || [];
  
  if (cards && cards.length) {
    grid.innerHTML = cards.map((c, idx) => `
      <div class="audition-card" onclick="applyAuditionByIndex(${idx})">
        <div class="audition-thumb-wrap">
          <img class="audition-thumb" src="${c.thumb}" />
        </div>
        <div class="audition-info">
          <div class="audition-name-row">
            <span class="audition-name">${c.name}</span>
            <span class="audition-tag">${c.tag}</span>
          </div>
          <div class="audition-desc">${c.desc}</div>
        </div>
      </div>
    `).join('');
  } else {
    grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-dim); padding: 40px;">Could not render presets on current frame</div>`;
  }
}

function closeAuditionModal() {
  document.getElementById('auditionModal').style.display = 'none';
}

function applyAuditionByIndex(idx) {
  if (!state.auditionCards || !state.auditionCards[idx]) return;
  let card = state.auditionCards[idx];
  applyAuditionProfile(card.settings, card.name);
}

function applyAuditionProfile(settings, name) {
  for (let k in settings) state.settings[k] = settings[k];

  if (settings.contrast !== undefined) {
    document.getElementById('slContrast').value = settings.contrast;
    document.getElementById('valContrast').innerText = settings.contrast.toFixed(2);
  }
  if (settings.saturation !== undefined) {
    document.getElementById('slSaturation').value = settings.saturation;
    document.getElementById('valSaturation').innerText = settings.saturation.toFixed(2);
  }
  if (settings.gamma !== undefined) {
    document.getElementById('slGamma').value = settings.gamma;
    document.getElementById('valGamma').innerText = settings.gamma.toFixed(2);
  }
  if (settings.brightness !== undefined) {
    document.getElementById('slBrightness').value = settings.brightness;
    document.getElementById('valBrightness').innerText = settings.brightness.toFixed(3);
  }
  if (settings.sharpness !== undefined) {
    document.getElementById('slSharpness').value = settings.sharpness;
    document.getElementById('valSharpness').innerText = settings.sharpness.toFixed(2);
  }
  if (settings.denoise !== undefined) {
    document.getElementById('slDenoise').value = settings.denoise;
    document.getElementById('valDenoise').innerText = settings.denoise.toFixed(1);
  }
  if (settings.grain !== undefined) {
    document.getElementById('slGrain').value = settings.grain;
    document.getElementById('valGrain').innerText = settings.grain.toFixed(2);
  }
  if (settings.temp !== undefined) {
    document.getElementById('slTemp').value = settings.temp;
    document.getElementById('valTemp').innerText = `${settings.temp > 0 ? '+' : ''}${settings.temp}`;
  }
  if (settings.crt_scanlines !== undefined) {
    document.getElementById('chkCrtScanlines').checked = settings.crt_scanlines;
    onToggleCRTScanlines(settings.crt_scanlines);
  }

  closeAuditionModal();
  updateLiveGPUGrade();
  showToast(`Applied '${name}' profile`);
  refreshFrame();
}

// =========================================================================
// TRIMMING & FILE ACTIONS
// =========================================================================
function markInPoint() {
  state.settings.trim_in = formatSec(state.currentSec);
  state.settings.trim_enabled = true;
  document.getElementById('valTrimIn').innerText = state.settings.trim_in;
  showToast(`Marked In Point at ${state.settings.trim_in}`);
}

function markOutPoint() {
  state.settings.trim_out = formatSec(state.currentSec);
  state.settings.trim_enabled = true;
  document.getElementById('valTrimOut').innerText = state.settings.trim_out;
  showToast(`Marked Out Point at ${state.settings.trim_out}`);
}

function resetTrim() {
  state.settings.trim_enabled = false;
  state.settings.trim_in = "00:00:00";
  state.settings.trim_out = "00:00:00";
  document.getElementById('valTrimIn').innerText = "00:00:00";
  document.getElementById('valTrimOut').innerText = "Full Video";
  showToast("Trim points reset to full media");
}

async function triggerAddFiles() {
  try {
    let res = await window.pywebview.api.add_files_dialog();
    if (res && res.queue) {
      state.queue = res.queue;
      state.activeIndex = res.active_index;
      updateBatchQueueUI();
      updateFolderNav();
      if (state.activeIndex >= 0) await selectMedia(state.activeIndex);
      showToast(`Loaded ${res.queue.length} items`);
    }
  } catch (e) {
    console.error("add_files error:", e);
  }
}

async function triggerAddFolder() {
  try {
    let res = await window.pywebview.api.add_folder_dialog();
    if (res && res.queue) {
      state.queue = res.queue;
      state.activeIndex = res.active_index;
      updateBatchQueueUI();
      updateFolderNav();
      if (state.activeIndex >= 0) await selectMedia(state.activeIndex);
      showToast(`Loaded folder with ${res.queue.length} items`);
    }
  } catch (e) {
    console.error("add_folder error:", e);
  }
}

function openOutputDir() {
  window.pywebview.api.open_output_folder();
}

function watchInPotPlayer() {
  let btn = document.getElementById('lblPotPlayerBtn');
  btn.innerText = 'Encoding Sample...';
  showToast("Rendering 30s sample with dual-audio & subtitles...");
  window.pywebview.api.watch_in_potplayer_color_graded(state.currentSec, state.settings, 30);
}

function renderQuickSample(sec) {
  showToast(`Rendering ${sec}s fast test sample...`);
  window.pywebview.api.watch_in_potplayer_color_graded(state.currentSec, state.settings, sec);
}

function onPotPlayerLaunched(ok, msg) {
  document.getElementById('lblPotPlayerBtn').innerText = 'Watch Remastered';
  showToast(msg);
}

// BATCH EXPORT
function toggleExport() {
  if (state.isEncoding) {
    window.pywebview.api.stop_batch_encode();
    document.getElementById('lblExportBtn').innerText = 'Export Remastered Media';
    document.getElementById('btnExportVideo').classList.remove('cancel');
    state.isEncoding = false;
    showToast("Export cancelled");
  } else {
    window.pywebview.api.start_batch_encode(state.settings);
    document.getElementById('lblExportBtn').innerText = 'Cancel Batch Export';
    document.getElementById('btnExportVideo').classList.add('cancel');
    state.isEncoding = true;
    showToast("Batch export started (NVIDIA RTX accelerated)");
  }
}

function onBatchProgress(t) {
  document.getElementById('telSpeed').innerText = `Speed: ${t.fps} fps (${t.multiplier}x)`;
  document.getElementById('telEta').innerText = `ETA: ${t.eta}`;
  document.getElementById('exportProgFill').style.width = `${t.percent}%`;
}

function onFileCompleted(idx, ok) {
  if (state.queue[idx]) {
    state.queue[idx].status = ok ? 'Done' : 'Failed';
    updateBatchQueueUI();
  }
}

function onBatchFinished(success) {
  state.isEncoding = false;
  document.getElementById('lblExportBtn').innerText = 'Export Remastered Media';
  document.getElementById('btnExportVideo').classList.remove('cancel');
  document.getElementById('exportProgFill').style.width = '100%';
  showToast(success ? "Batch export finished successfully!" : "Batch export stopped");
  updateBatchQueueUI();
}
</script>
</body>
</html>
"""

def start_app():
    backend = UniversalStudioBackend()
    
    icon_path = os.path.join(get_base_dir(), "apple_logo.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(get_base_dir(), "apple upscaler", "apple_logo.ico")

    window_title = BRANDING.get("window_title", "Apple Upscaler Pro - Universal Anime & Film AI Remaster")

    window = webview.create_window(
        title=window_title,
        html=HTML_UI,
        js_api=backend,
        width=1480,
        height=950,
        min_size=(1140, 750),
        background_color="#0c090a"
    )
    webview.start(debug=False)

if __name__ == "__main__":
    start_app()
