#!/usr/bin/env python3
"""Prepare SoulGold G2 Cyndaquil Rich Ambient assets.

G2 keeps the G1 renderer contract sealed and expands only the body-behavior
asset set: Idle, Walk, LookUp, DeepBreath and Rotate. All selected actions are
single-OBJ-safe at <=64x64. Frames are still remapped to SoulGold's existing
Cyndaquil palette so palette ownership remains deferred.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
ACTIONS = ("Idle", "Walk", "LookUp", "DeepBreath", "Rotate")


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
            raise SystemExit(f"Missing converted action directory: {src}")
        shutil.copytree(src, target / action.lower())
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

    converter = framework / "tools" / "pmd_gba_converter.py"
    remapper = framework / "tools" / "pmd_gba_remap_host_palette.py"
    emitter = framework / "tools" / "emit_soulgold_g2_c.py"
    action_arg = ",".join(ACTIONS)

    variants = (
        ("player", "UpRight"),
        ("opponent", "DownLeft"),
    )

    summary: dict[str, object] = {
        "phase": "G2_RICH_AMBIENT",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "species": "Cyndaquil",
        "actions": list(ACTIONS),
        "home_source": "Idle frame 0",
        "palette_policy": "remap_to_existing_soulgold_cyndaquil_palette",
        "renderer_contract": "two_slot_rolling_cache_MAX_MON_PIC_FRAMES_unchanged",
        "variants": {},
    }

    for variant, direction in variants:
        variant_dir = work / variant
        run([
            sys.executable, str(converter),
            "--source", str(species_dir),
            "--output", str(variant_dir),
            "--species", "Cyndaquil",
            "--national-dex", "155",
            "--actions", action_arg,
            "--direction", direction,
            "--source-revision", SPRITECOLLAB_REV,
            "--source-repo-path", "sprite/0155",
            "--host-asset-root", f"graphics/pmd/cyndaquil/{variant}",
        ])
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

        manifest = json.loads((variant_dir / "manifest.ir.json").read_text(encoding="utf-8"))
        summary["variants"][variant] = {
            "direction": direction,
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

    (out / "G2_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared SoulGold G2 Rich Ambient staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
