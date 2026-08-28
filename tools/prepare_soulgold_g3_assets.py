#!/usr/bin/env python3
"""Prepare SoulGold G3R3 two-sided grounded PMD battle assets.

Acceptance target:
- player Cyndaquil: PMD UpRight;
- opponent Marill: PMD DownLeft;
- both use HOME + Idle/Walk/Nod/Rotate;
- every grounded frame is normalized by PMD's white shadow-origin marker;
- PMD body+shadow remain one atomic 64x64 frame;
- runtime presentation offsets remain zero.

Pose is deliberately excluded. It is unnecessary for the renderer/ownership
proof and Cyndaquil's Pose uses a different PMD ground origin, making it a poor
candidate for the first stable grounded ecology gate.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
ACTIONS = ("Idle", "Walk", "Nod", "Rotate")
DIRECTIONS = ["Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft"]

TARGETS = (
    {
        "species": "Cyndaquil",
        "slug": "cyndaquil",
        "dex": "155",
        "spritecollab_id": "0155",
        "variant": "player",
        "direction": "UpRight",
    },
    {
        "species": "Marill",
        "slug": "marill",
        "dex": "183",
        "spritecollab_id": "0183",
        "variant": "opponent",
        "direction": "DownLeft",
    },
)


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def require_revision(repo: Path, expected: str, label: str) -> None:
    actual = git_head(repo)
    if actual != expected:
        raise SystemExit(f"{label} revision mismatch: expected {expected}, got {actual}")


def parse_action_geometry(anim_xml: Path) -> tuple[int, dict[str, tuple[int, int, int]]]:
    root = ET.parse(anim_xml).getroot()
    shadow_node = root.find("ShadowSize")
    if shadow_node is None or shadow_node.text is None:
        raise SystemExit(f"ShadowSize missing: {anim_xml}")
    shadow_size = int(shadow_node.text)
    if shadow_size < 0 or shadow_size > 2:
        raise SystemExit(f"Invalid ShadowSize={shadow_size}: {anim_xml}")

    out: dict[str, tuple[int, int, int]] = {}
    for anim in root.findall("./Anims/Anim"):
        name = anim.findtext("Name")
        if name not in ACTIONS:
            continue
        w = anim.findtext("FrameWidth")
        h = anim.findtext("FrameHeight")
        durations = anim.findall("./Durations/Duration")
        if w is None or h is None or not durations:
            raise SystemExit(f"Grounded action lacks geometry/durations: {name} in {anim_xml}")
        out[name] = (int(w), int(h), len(durations))
    missing = [a for a in ACTIONS if a not in out]
    if missing:
        raise SystemExit(f"Missing grounded actions {missing}: {anim_xml}")
    return shadow_size, out


def audit_shadow_source(species_dir: Path, direction: str) -> dict[str, object]:
    shadow_size, geometry = parse_action_geometry(species_dir / "AnimData.xml")
    row = DIRECTIONS.index(direction)
    audit: dict[str, object] = {"shadow_size": shadow_size, "actions": {}}

    for action in ACTIONS:
        w, h, frames = geometry[action]
        sheet = Image.open(species_dir / f"{action}-Shadow.png").convert("RGBA")
        records = []
        for i in range(frames):
            crop = sheet.crop((i * w, row * h, (i + 1) * w, (row + 1) * h))
            white = []
            active = 0
            px = crop.load()
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    if a != 255:
                        continue
                    if r == 255 and g == 255 and b == 255:
                        white.append((x, y))
                    elif g == 255 or (r == 255 and shadow_size > 0) or (b == 255 and shadow_size > 1):
                        active += 1
            if len(white) != 1:
                raise SystemExit(
                    f"Expected exactly one PMD white shadow origin: {species_dir.name}/{action}/{direction}/frame{i}; got {white}"
                )
            if active <= 0:
                raise SystemExit(
                    f"No active PMD shadow pixels: {species_dir.name}/{action}/{direction}/frame{i}"
                )
            records.append({"frame": i, "shadow_origin": list(white[0]), "active_shadow_pixels": active})
        audit["actions"][action] = records
    return audit


def copy_variant_assets(variant_dir: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for action in ACTIONS:
        shutil.copytree(variant_dir / action.lower(), target / action.lower())
    shutil.copy2(variant_dir / "manifest.ir.json", target / "manifest.ir.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    spritecollab = args.spritecollab.resolve()
    soulgold = args.soulgold.resolve()
    out = args.output.resolve()
    framework = args.framework_root.resolve()

    require_revision(spritecollab, SPRITECOLLAB_REV, "SpriteCollab")
    require_revision(soulgold, SOULGOLD_REV, "SoulGold")

    if out.exists():
        shutil.rmtree(out)
    work = out / "work"
    staging = out / "staging"
    work.mkdir(parents=True)
    (staging / "src").mkdir(parents=True)

    converter = framework / "tools" / "convert_soulgold_g3.py"
    remapper = framework / "tools" / "pmd_gba_remap_host_palette.py"
    emitter = framework / "tools" / "emit_soulgold_g3_c.py"
    action_arg = ",".join(ACTIONS)

    summary: dict[str, object] = {
        "phase": "G3R3_TWO_SIDED_GROUNDED",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "actions": list(ACTIONS),
        "ground_anchor": "PMD Shadow.png white origin",
        "runtime_offset_policy": "grounded ambient presentationX=0 presentationY=0",
        "renderer_contract": "two-slot rolling cache",
        "targets": {},
    }

    for target in TARGETS:
        species = target["species"]
        slug = target["slug"]
        variant = target["variant"]
        direction = target["direction"]
        species_dir = spritecollab / "sprite" / target["spritecollab_id"]
        host_palette = soulgold / "graphics" / "pokemon" / slug / "normal.pal"
        if not (species_dir / "AnimData.xml").is_file():
            raise SystemExit(f"Missing {species} AnimData.xml: {species_dir}")
        if not host_palette.is_file():
            raise SystemExit(f"Missing SoulGold {species} palette: {host_palette}")

        shadow_audit = audit_shadow_source(species_dir, direction)
        variant_dir = work / f"{slug}_{variant}"
        run([
            sys.executable, str(converter),
            "--source", str(species_dir),
            "--species", species,
            "--national-dex", target["dex"],
            "--actions", action_arg,
            "--direction", direction,
            "--source-revision", SPRITECOLLAB_REV,
            "--source-repo-path", f"sprite/{target['spritecollab_id']}",
            "--output", str(variant_dir),
            "--host-asset-root", f"graphics/pmd/{slug}/{variant}",
        ])

        run([
            sys.executable, str(remapper),
            "--frames-root", str(variant_dir),
            "--host-palette", str(host_palette),
        ])

        generated_c = staging / "src" / f"pmd_{slug}_{variant}_ambient.c"
        run([
            sys.executable, str(emitter),
            "--ir", str(variant_dir / "manifest.ir.json"),
            "--output", str(generated_c),
            "--variant", variant,
            "--asset-root", f"graphics/pmd/{slug}/{variant}",
        ])

        copy_variant_assets(
            variant_dir,
            staging / "graphics" / "pmd" / slug / variant,
        )

        manifest = json.loads((variant_dir / "manifest.ir.json").read_text(encoding="utf-8"))
        summary["targets"][f"{species}_{variant}"] = {
            "species": species,
            "variant": variant,
            "direction": direction,
            "host_palette": f"graphics/pokemon/{slug}/normal.pal",
            "shadow_source_audit": shadow_audit,
            "manifest_shadow": manifest.get("shadow"),
            "actions": {
                action: {
                    "frame_count": len(manifest["actions"][action]["frames"]),
                    "durations": [f["duration"] for f in manifest["actions"][action]["frames"]],
                    "source_origins": [
                        [f["source_center_x"], f["source_center_y"]]
                        for f in manifest["actions"][action]["frames"]
                    ],
                }
                for action in ACTIONS
            },
        }

    (out / "G3_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared SoulGold G3R3 two-sided PMD staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
