#!/usr/bin/env python3
"""Ingest Pokémon Showdown animated battle GIFs into GBA-friendly assets.

S0 goals:
- accept official sprites.zip (or a locally extracted source tree)
- preserve a stable whole-GIF coordinate system to avoid frame jitter
- fit each animation into a 64x64 battler canvas without upscaling
- use one shared 15-color + transparent palette per animation
- preserve GIF frame timing, quantized to 60 Hz GBA ticks
- emit PNG previews, raw 4bpp tiles, BGR555 palette, and JSON manifest

This tool intentionally does not patch SoulGold yet. S1 owns runtime integration.
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

OFFICIAL_ZIP_URL = "https://www.pokemonshowdown.com/files/resources/sprites.zip"
LANE_DIRS = {
    "front": "ani",
    "back": "ani-back",
    "front-shiny": "ani-shiny",
    "back-shiny": "ani-back-shiny",
}
GBA_CANVAS = 64
GBA_TICK_MS = 1000.0 / 60.0
TRANSPARENT_RGBA = (0, 0, 0, 0)


@dataclass(frozen=True)
class FrameInfo:
    image: Image.Image
    duration_ms: int


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--zip", type=Path, help="Path to official Showdown sprites.zip")
    src.add_argument("--source-dir", type=Path, help="Extracted directory containing ani/ etc.")
    src.add_argument("--download", action="store_true", help="Download official sprites.zip first")
    p.add_argument("--cache-dir", type=Path, default=Path(".cache/showdown"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--species", nargs="+", required=True,
                   help="Showdown file stems, e.g. cyndaquil pikachu charizard-mega-x")
    p.add_argument("--lanes", nargs="+", choices=sorted(LANE_DIRS), default=["front", "back"])
    p.add_argument("--force", action="store_true")
    return p.parse_args()


def download_zip(cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    dst = cache_dir / "sprites.zip"
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    tmp = dst.with_suffix(".zip.part")
    req = urllib.request.Request(OFFICIAL_ZIP_URL, headers={"User-Agent": "SoulGold-Showdown-Prototype/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as f:
        shutil.copyfileobj(r, f)
    tmp.replace(dst)
    return dst


def find_zip_member(zf: zipfile.ZipFile, lane_dir: str, species: str) -> str:
    wanted = f"{lane_dir}/{species}.gif".lower()
    matches = [n for n in zf.namelist() if n.lower().endswith(wanted)]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected exactly one *{wanted} in zip, found {len(matches)}")
    return matches[0]


def find_source_file(root: Path, lane_dir: str, species: str) -> Path:
    direct = root / lane_dir / f"{species}.gif"
    if direct.is_file():
        return direct
    matches = list(root.glob(f"**/{lane_dir}/{species}.gif"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected exactly one {lane_dir}/{species}.gif below {root}, found {len(matches)}")
    return matches[0]


def read_gif(data: bytes) -> tuple[list[FrameInfo], tuple[int, int]]:
    frames: list[FrameInfo] = []
    with Image.open(io.BytesIO(data)) as im:
        source_size = im.size
        n = getattr(im, "n_frames", 1)
        for i in range(n):
            im.seek(i)
            duration = int(im.info.get("duration", 100) or 100)
            frames.append(FrameInfo(im.convert("RGBA").copy(), duration))
    if not frames:
        raise ValueError("GIF has no frames")
    return frames, source_size


def fit_scale(source_size: tuple[int, int]) -> float:
    w, h = source_size
    if w <= 0 or h <= 0:
        raise ValueError(f"Invalid source size {source_size}")
    return min(1.0, GBA_CANVAS / w, GBA_CANVAS / h)


def transform_frames(frames: list[FrameInfo], source_size: tuple[int, int]) -> list[FrameInfo]:
    scale = fit_scale(source_size)
    sw, sh = source_size
    rw = max(1, int(round(sw * scale)))
    rh = max(1, int(round(sh * scale)))
    x = (GBA_CANVAS - rw) // 2
    y = GBA_CANVAS - rh
    out: list[FrameInfo] = []
    for f in frames:
        src = f.image
        if src.size != source_size:
            tmp = Image.new("RGBA", source_size, TRANSPARENT_RGBA)
            tmp.alpha_composite(src, (0, 0))
            src = tmp
        if scale != 1.0:
            src = src.resize((rw, rh), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (GBA_CANVAS, GBA_CANVAS), TRANSPARENT_RGBA)
        canvas.alpha_composite(src, (x, y))
        out.append(FrameInfo(canvas, f.duration_ms))
    return out


def make_shared_palette(frames: list[FrameInfo]) -> list[tuple[int, int, int]]:
    opaque: list[tuple[int, int, int]] = []
    seen = set()
    for f in frames:
        for r, g, b, a in f.image.getdata():
            if a < 128:
                continue
            rgb = (r, g, b)
            if rgb not in seen:
                seen.add(rgb)
                opaque.append(rgb)
    if not opaque:
        return []
    if len(opaque) <= 15:
        return opaque

    samples: list[tuple[int, int, int]] = []
    for f in frames:
        for r, g, b, a in f.image.getdata():
            if a >= 128:
                samples.append((r, g, b))
    strip = Image.new("RGB", (len(samples), 1))
    strip.putdata(samples)
    q = strip.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[: 15 * 3]
    used = sorted(set(q.getdata()))
    colors = [tuple(pal[i * 3:i * 3 + 3]) for i in used]
    return colors[:15]


def nearest_color(rgb: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> int:
    r, g, b = rgb
    best_i = 0
    best_d = 1 << 60
    for i, (pr, pg, pb) in enumerate(palette):
        d = (r-pr)*(r-pr) + (g-pg)*(g-pg) + (b-pb)*(b-pb)
        if d < best_d:
            best_d = d
            best_i = i
    return best_i


def index_frame(img: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    out = Image.new("P", img.size, 0)
    pal_bytes = [0, 0, 0]
    for c in palette:
        pal_bytes.extend(c)
    pal_bytes.extend([0] * (768 - len(pal_bytes)))
    out.putpalette(pal_bytes)
    indices = []
    for r, g, b, a in img.getdata():
        if a < 128 or not palette:
            indices.append(0)
        else:
            indices.append(nearest_color((r, g, b), palette) + 1)
    out.putdata(indices)
    out.info["transparency"] = 0
    return out


def gba_bgr555(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    r5 = (r * 31 + 127) // 255
    g5 = (g * 31 + 127) // 255
    b5 = (b * 31 + 127) // 255
    return r5 | (g5 << 5) | (b5 << 10)


def encode_palette(palette: list[tuple[int, int, int]]) -> bytes:
    values = [0] + [gba_bgr555(c) for c in palette]
    values += [0] * (16 - len(values))
    return b"".join(v.to_bytes(2, "little") for v in values[:16])


def encode_4bpp(img: Image.Image) -> bytes:
    if img.mode != "P" or img.size != (64, 64):
        raise ValueError("4bpp encoder requires indexed 64x64 image")
    px = list(img.getdata())
    out = bytearray()
    for ty in range(0, 64, 8):
        for tx in range(0, 64, 8):
            for y in range(8):
                row = (ty + y) * 64 + tx
                for x in range(0, 8, 2):
                    lo = px[row + x] & 0xF
                    hi = px[row + x + 1] & 0xF
                    out.append(lo | (hi << 4))
    if len(out) != 2048:
        raise AssertionError(f"Expected 2048-byte 64x64 4bpp frame, got {len(out)}")
    return bytes(out)


def ms_to_ticks(ms: int) -> int:
    return max(1, int(round(ms / GBA_TICK_MS)))


def ingest_one(data: bytes, species: str, lane: str, out_root: Path, source_desc: str) -> dict:
    raw_frames, source_size = read_gif(data)
    frames = transform_frames(raw_frames, source_size)
    palette = make_shared_palette(frames)
    indexed = [index_frame(f.image, palette) for f in frames]

    out_dir = out_root / species / lane
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "palette.pal").write_bytes(encode_palette(palette))

    frame_records = []
    for i, (f, idx) in enumerate(zip(frames, indexed)):
        png_name = f"frame_{i:03d}.png"
        bin_name = f"frame_{i:03d}.4bpp"
        idx.save(out_dir / png_name, transparency=0)
        (out_dir / bin_name).write_bytes(encode_4bpp(idx))
        frame_records.append({
            "index": i,
            "duration_ms": f.duration_ms,
            "duration_ticks_60hz": ms_to_ticks(f.duration_ms),
            "png": png_name,
            "tiles_4bpp": bin_name,
        })

    manifest = {
        "format": "soulgold-showdown-s0-v1",
        "species": species,
        "lane": lane,
        "source": source_desc,
        "source_canvas": list(source_size),
        "gba_canvas": [64, 64],
        "scale": fit_scale(source_size),
        "anchor": "bottom-center",
        "palette_entries_visible": len(palette),
        "palette_entries_total": 16,
        "frame_count": len(frames),
        "loop_ticks_60hz": sum(r["duration_ticks_60hz"] for r in frame_records),
        "frames": frame_records,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    args = parse_args()
    if args.output.exists() and any(args.output.iterdir()) and not args.force:
        raise SystemExit(f"Output {args.output} is not empty; use --force")
    args.output.mkdir(parents=True, exist_ok=True)

    zip_path: Path | None = None
    if args.download:
        zip_path = download_zip(args.cache_dir)
    elif args.zip:
        zip_path = args.zip

    results = []
    if zip_path:
        with zipfile.ZipFile(zip_path) as zf:
            for species in args.species:
                for lane in args.lanes:
                    lane_dir = LANE_DIRS[lane]
                    member = find_zip_member(zf, lane_dir, species)
                    results.append(ingest_one(zf.read(member), species, lane, args.output,
                                              f"sprites.zip:{member}"))
    else:
        assert args.source_dir is not None
        for species in args.species:
            for lane in args.lanes:
                lane_dir = LANE_DIRS[lane]
                src = find_source_file(args.source_dir, lane_dir, species)
                results.append(ingest_one(src.read_bytes(), species, lane, args.output, str(src)))

    summary = {
        "format": "soulgold-showdown-s0-summary-v1",
        "official_source": OFFICIAL_ZIP_URL,
        "animations": results,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: emitted {len(results)} animation(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
