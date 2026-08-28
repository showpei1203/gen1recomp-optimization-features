#!/usr/bin/env python3
"""Prepare SoulGold G3 Cyndaquil battle-facing-compatible Rich Ambient assets.

Human visual acceptance established the following rule:
- battle ambient actions must have a real directional PMD sheet;
- player uses the UpRight row and opponent uses DownLeft;
- an action may turn naturally during its sequence, but must return cleanly to
  the same 45-degree HOME afterward;
- shared single-row/non-directional actions are banned from battle ambient;
- authentic PMD per-frame shadows are composited under the body before GBA
  normalization, using SpriteBot-compatible ShadowSize marker rules.

Audited directional set for Cyndaquil G3:
Idle / Walk / Nod / Pose / Rotate.
Rotate is intentionally retained because it naturally turns back to HOME.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
ACTIONS = ("Idle", "Walk", "Nod", "Pose", "Rotate")
BANNED_AMBIENT_ACTIONS = ("LookUp", "DeepBreath", "Sit")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def require_revision(repo: Path, expected: str, label: str) -> None:
    actual = git_head(repo)
    if actual != expected:
        raise SystemExit(f"{label} revision mismatch: expected {expected}, got {actual}")


def copy_variant_assets(variant_dir: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for action in ACTIONS:
        src = variant_dir / action.lower()
        if not src.is_dir():
            raise SystemExit(f"Missing converted G3 action directory: {src}")
        shutil.copytree(src, target / action.lower())
    shutil.copy2(variant_dir / "manifest.ir.json", target / "manifest.ir.json")


def shadow_alpha_delta(shadowed: Path, body_only: Path) -> int:
    """Count pixels made opaque specifically by the PMD shadow compositor."""
    a = Image.open(shadowed).convert("RGBA")
    b = Image.open(body_only).convert("RGBA")
    if a.size != b.size:
        raise SystemExit(f"Shadow audit size mismatch: {shadowed}={a.size}, {body_only}={b.size}")
    ap = a.load()
    bp = b.load()
    count = 0
    for y in range(a.height):
        for x in range(a.width):
            if ap[x, y][3] > 0 and bp[x, y][3] == 0:
                count += 1
    return count


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

    species_dir = spritecollab / "sprite" / "0155"
    host_palette = soulgold / "graphics" / "pokemon" / "cyndaquil" / "normal.pal"
    if not (species_dir / "AnimData.xml").is_file():
        raise SystemExit(f"Missing Cyndaquil AnimData.xml: {species_dir}")
    if not host_palette.is_file():
        raise SystemExit(f"Missing SoulGold Cyndaquil palette: {host_palette}")

    if out.exists():
        shutil.rmtree(out)
    work = out / "work"
    staging = out / "staging"
    work.mkdir(parents=True)
    (staging / "graphics" / "pmd" / "cyndaquil").mkdir(parents=True)
    (staging / "src").mkdir(parents=True)

    converter = framework / "tools" / "convert_soulgold_g3.py"
    body_only_converter = framework / "tools" / "pmd_gba_converter.py"
    remapper = framework / "tools" / "pmd_gba_remap_host_palette.py"
    emitter = framework / "tools" / "emit_soulgold_g3_c.py"
    action_arg = ",".join(ACTIONS)

    variants = (("player", "UpRight"), ("opponent", "DownLeft"))

    summary: dict[str, object] = {
        "phase": "G3R1_BATTLE_FACING_SENDOUT_SHADOW",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "species": "Cyndaquil",
        "actions": list(ACTIONS),
        "banned_from_ambient": list(BANNED_AMBIENT_ACTIONS),
        "direction_policy": "real_directional_sheet; 45-degree HOME start/end; transitional turning allowed when naturally returning",
        "shadow_policy": "authentic PMD per-frame Shadow.png mask, SpriteBot-compatible ShadowSize rules, composited below body",
        "shadow_pixel_gate": "every emitted frame must add >0 opaque pixels versus an otherwise-identical body-only conversion",
        "home_source": "Idle frame 0",
        "palette_policy": "remap_combined_body_shadow_to_existing_soulgold_cyndaquil_palette",
        "renderer_contract": "G1 two-slot rolling cache SEALED/REUSED",
        "variants": {},
    }

    for variant, direction in variants:
        variant_dir = work / variant
        body_only_dir = work / f"{variant}_body_only"
        common_args = [
            "--source", str(species_dir),
            "--species", "Cyndaquil",
            "--national-dex", "155",
            "--actions", action_arg,
            "--direction", direction,
            "--source-revision", SPRITECOLLAB_REV,
            "--source-repo-path", "sprite/0155",
        ]

        run([
            sys.executable, str(converter),
            *common_args,
            "--output", str(variant_dir),
            "--host-asset-root", f"graphics/pmd/cyndaquil/{variant}",
        ])
        run([
            sys.executable, str(body_only_converter),
            *common_args,
            "--output", str(body_only_dir),
            "--host-asset-root", f"graphics/pmd/cyndaquil/{variant}_body_only",
        ])

        manifest = json.loads((variant_dir / "manifest.ir.json").read_text(encoding="utf-8"))
        if manifest.get("shadow", {}).get("shadow_size") != 1:
            raise SystemExit(f"Unexpected Cyndaquil PMD ShadowSize metadata: {manifest.get('shadow')}")

        shadow_counts: dict[str, list[int]] = {}
        for action in ACTIONS:
            counts = []
            frames = manifest["actions"][action]["frames"]
            for frame in frames:
                idx = int(frame["index"])
                shadowed = variant_dir / action.lower() / f"frame_{idx:02d}.png"
                body_only = body_only_dir / action.lower() / f"frame_{idx:02d}.png"
                extra = shadow_alpha_delta(shadowed, body_only)
                if extra <= 0:
                    raise SystemExit(
                        f"PMD shadow pixel gate FAIL: {variant}/{action}/frame_{idx:02d} adds {extra} opaque shadow pixels"
                    )
                counts.append(extra)
            shadow_counts[action] = counts

        # Palette remap is deliberately after the alpha-delta gate. Remapping
        # changes RGB indices but preserves alpha, so a proven non-empty shadow
        # remains a visible opaque part of the final GBA frame.
        run([
            sys.executable, str(remapper),
            "--frames-root", str(variant_dir),
            "--host-palette", str(host_palette),
        ])

        generated_c = staging / "src" / f"pmd_cyndaquil_{variant}_ambient.c"
        run([
            sys.executable, str(emitter),
            "--ir", str(variant_dir / "manifest.ir.json"),
            "--output", str(generated_c),
            "--variant", variant,
            "--asset-root", f"graphics/pmd/cyndaquil/{variant}",
        ])

        copy_variant_assets(
            variant_dir,
            staging / "graphics" / "pmd" / "cyndaquil" / variant,
        )

        summary["variants"][variant] = {
            "direction": direction,
            "shadow": manifest["shadow"],
            "shadow_extra_opaque_pixels": shadow_counts,
            "actions": {
                action: {
                    "frame_count": len(manifest["actions"][action]["frames"]),
                    "durations": [f["duration"] for f in manifest["actions"][action]["frames"]],
                    "source_size": [
                        manifest["actions"][action]["source_frame_width"],
                        manifest["actions"][action]["source_frame_height"],
                    ],
                }
                for action in ACTIONS
            },
        }

    (out / "G3_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared SoulGold G3R1 directional+shadow staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
