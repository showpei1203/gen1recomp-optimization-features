#!/usr/bin/env python3
"""SoulGold G3 strict directional converter with authentic PMD shadows.

G3 keeps the sealed base converter unchanged. For every *-Anim.png load, this
wrapper composites the matching *-Shadow.png underneath the body using the same
rules used by PMDCollab SpriteBot previews:
- green shadow pixels are always active;
- red pixels are active when ShadowSize > 0;
- blue pixels are active when ShadowSize > 1.

Cyndaquil has ShadowSize=1, therefore green+red markers become opaque black
shadow pixels. The combined sheet then follows the normal strict 8-direction
crop, PMD body-center anchor normalization and GBA palette remap pipeline.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

import pmd_gba_converter as base

_original_open_rgba = base._open_rgba
_original_convert = base.convert
_shadow_size_cache: dict[Path, int] = {}


def shadow_size_for_species(source_dir: Path) -> int:
    source_dir = source_dir.resolve()
    if source_dir in _shadow_size_cache:
        return _shadow_size_cache[source_dir]

    root = ET.parse(source_dir / "AnimData.xml").getroot()
    node = root.find("ShadowSize")
    if node is None or node.text is None:
        raise ValueError(f"ShadowSize missing in {source_dir / 'AnimData.xml'}")
    value = int(node.text)
    if value < 0 or value > 2:
        raise ValueError(f"Invalid PMD ShadowSize={value}")
    _shadow_size_cache[source_dir] = value
    return value


def build_shadow_mask(shadow: Image.Image, shadow_size: int) -> Image.Image:
    src = shadow.convert("RGBA")
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    spx = src.load()
    dpx = out.load()

    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = spx[x, y]
            if a != 255:
                continue

            active = False
            if g == 255:
                active = True
            elif r == 255 and shadow_size > 0:
                active = True
            elif b == 255 and shadow_size > 1:
                active = True

            if active:
                dpx[x, y] = (0, 0, 0, 255)

    return out


def open_rgba_with_shadow(path: Path) -> Image.Image:
    body = _original_open_rgba(path)
    if not path.name.endswith("-Anim.png"):
        return body

    shadow_path = path.with_name(path.name.replace("-Anim.png", "-Shadow.png"))
    if not shadow_path.is_file():
        raise FileNotFoundError(f"Missing PMD shadow sheet for battle asset: {shadow_path}")

    shadow = _original_open_rgba(shadow_path)
    if shadow.size != body.size:
        raise ValueError(
            f"PMD shadow/body layout mismatch for {path.stem}: body={body.size}, shadow={shadow.size}"
        )

    mask = build_shadow_mask(shadow, shadow_size_for_species(path.parent))
    combined = Image.new("RGBA", body.size, (0, 0, 0, 0))
    combined.alpha_composite(mask)
    combined.alpha_composite(body)
    return combined


def convert_with_shadow_metadata(args):
    rc = _original_convert(args)
    if args.metadata_only:
        return rc

    manifest = args.output.resolve() / "manifest.ir.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["shadow"] = {
        "source": "PMDCollab per-action *-Shadow.png",
        "shadow_size": shadow_size_for_species(args.source.resolve()),
        "render_policy": "SpriteBot-compatible marker mask composited below body before 64x64 normalization",
        "separate_obj": False,
        "body_shadow_frame_sync": "atomic_same_frame",
    }
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return rc


base._open_rgba = open_rgba_with_shadow
base.convert = convert_with_shadow_metadata

if __name__ == "__main__":
    raise SystemExit(base.main())
