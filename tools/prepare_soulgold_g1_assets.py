#!/usr/bin/env python3
"""Prepare the SoulGold G1 Cyndaquil rolling-cache asset bundle.

Inputs:
- a local PMDCollab/SpriteCollab checkout pinned to the authority revision;
- a SoulGold checkout pinned to the G1 baseline.

Outputs a staging directory that install_soulgold_g1.py can copy into SoulGold.
G1 intentionally prepares only Walk, separately for player/opponent directions,
and remaps frames to SoulGold's existing Cyndaquil palette so renderer/cache
validation is isolated from PMD palette ownership.
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


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def require_revision(repo: Path, expected: str, label: str) -> None:
    actual = git_head(repo)
    if actual != expected:
        raise SystemExit(f"{label} revision mismatch: expected {expected}, got {actual}")


def copy_variant_assets(variant_dir: Path, staging_graphics: Path) -> None:
    target = staging_graphics / variant_dir.name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(variant_dir / "walk", target / "walk")
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
    emitter = framework / "tools" / "pmd_gba_emit_c.py"

    variants = (
        ("player", "UpRight"),
        ("opponent", "DownLeft"),
    )

    summary: dict[str, object] = {
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "species": "Cyndaquil",
        "actions": ["Walk"],
        "variants": {},
        "g1_palette_policy": "remap_to_existing_soulgold_cyndaquil_palette",
    }

    for variant, direction in variants:
        variant_dir = work / variant
        run([
            sys.executable, str(converter),
            "--source", str(species_dir),
            "--output", str(variant_dir),
            "--species", "Cyndaquil",
            "--national-dex", "155",
            "--actions", "Walk",
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

        generated_c = staging / "src" / f"pmd_cyndaquil_{variant}_walk.c"
        run([
            sys.executable, str(emitter),
            "--ir", str(variant_dir / "manifest.ir.json"),
            "--output", str(generated_c),
            "--variant", variant,
            "--asset-root", f"graphics/pmd/cyndaquil/{variant}",
            "--actions", "Walk",
        ])
        copy_variant_assets(variant_dir, staging / "graphics" / "pmd" / "cyndaquil")

        manifest = json.loads((variant_dir / "manifest.ir.json").read_text(encoding="utf-8"))
        walk = manifest["actions"]["Walk"]
        summary["variants"][variant] = {
            "direction": direction,
            "frame_count": len(walk["frames"]),
            "durations": [f["duration"] for f in walk["frames"]],
            "source_size": [walk["source_frame_width"], walk["source_frame_height"]],
        }

    (out / "G1_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared SoulGold G1 staging bundle: {staging}")
    print("Expected proof: 4 PMD Walk frames played through only 2 resident battler image slots.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
