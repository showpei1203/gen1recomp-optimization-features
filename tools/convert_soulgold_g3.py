#!/usr/bin/env python3
"""SoulGold G3 strict directional converter with authentic PMD shadows.

G3 keeps the sealed base converter unchanged. This wrapper adds two PMD-native
semantics for grounded battle ambient frames:
- composite the matching *-Shadow.png underneath the body using SpriteBot's
  ShadowSize rules;
- use the WHITE shadow-origin marker as the normalization anchor instead of the
  green body-center marker from *-Offsets.png.

The second rule is essential for grounded actions. Locking body-center removes
body motion but moves the feet/shadow around the battlefield. Locking PMD's
shadow origin keeps the battler planted while preserving body motion inside the
64x64 frame. Jump/float actions will use a different policy in a later gate.
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


def shadow_origin_sheet(shadow: Image.Image) -> Image.Image:
    """Translate PMD white shadow-origin markers into base-converter anchors.

    The sealed base converter asks body_center_from_offsets() for green pixels.
    Rather than changing that shared code, G3 supplies a synthetic offsets sheet
    containing only one green pixel at every PMD white shadow-origin marker.
    This preserves the base converter while giving grounded G3 the correct
    PMD coordinate authority.
    """
    src = shadow.convert("RGBA")
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    spx = src.load()
    dpx = out.load()
    count = 0

    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = spx[x, y]
            if a == 255 and r == 255 and g == 255 and b == 255:
                dpx[x, y] = (0, 255, 0, 255)
                count += 1

    if count == 0:
        raise ValueError("No PMD white shadow-origin markers found")
    return out


def open_rgba_with_shadow(path: Path) -> Image.Image:
    body = _original_open_rgba(path)

    if path.name.endswith("-Offsets.png"):
        shadow_path = path.with_name(path.name.replace("-Offsets.png", "-Shadow.png"))
        if not shadow_path.is_file():
            raise FileNotFoundError(f"Missing PMD shadow sheet for ground anchor: {shadow_path}")
        shadow = _original_open_rgba(shadow_path)
        if shadow.size != body.size:
            raise ValueError(
                f"PMD shadow/offset layout mismatch for {path.stem}: offsets={body.size}, shadow={shadow.size}"
            )
        return shadow_origin_sheet(shadow)

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
        "ground_anchor": "PMD white shadow-origin marker",
        "grounding_policy": "grounded ambient locks shadow origin; body motion remains inside frame",
        "separate_obj": False,
        "body_shadow_frame_sync": "atomic_same_frame",
    }
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return rc


base._open_rgba = open_rgba_with_shadow
base.convert = convert_with_shadow_metadata

if __name__ == "__main__":
    raise SystemExit(base.main())
