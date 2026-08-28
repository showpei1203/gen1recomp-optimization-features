#!/usr/bin/env python3
"""Prepare Cyndaquil Showdown front/back idle assets for SoulGold S1.

The official sprites.zip is the source authority. S1 remaps the converted GIF
frames to SoulGold's existing Cyndaquil palette so the first runtime experiment
changes body pixels/timing only and does not yet assume palette ownership.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def require_revision(repo: Path) -> None:
    actual = git_head(repo)
    if actual != SOULGOLD_REV:
        raise SystemExit(f"SoulGold revision mismatch: expected {SOULGOLD_REV}, got {actual}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprites-zip", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    framework = args.framework_root.resolve()
    out = args.output.resolve()
    sprites_zip = args.sprites_zip.resolve()
    require_revision(soulgold)
    if not sprites_zip.is_file():
        raise SystemExit(f"Missing sprites.zip: {sprites_zip}")

    host_palette = soulgold / "graphics" / "pokemon" / "cyndaquil" / "normal.pal"
    if not host_palette.is_file():
        raise SystemExit(f"Missing SoulGold Cyndaquil palette: {host_palette}")

    if out.exists():
        shutil.rmtree(out)
    ingest = out / "ingest"
    staging = out / "staging"
    graphics = staging / "graphics" / "showdown" / "cyndaquil"
    src = staging / "src"
    src.mkdir(parents=True, exist_ok=True)

    run([
        sys.executable, str(framework / "tools" / "showdown_sprites_ingest.py"),
        "--zip", str(sprites_zip),
        "--output", str(ingest),
        "--species", "cyndaquil",
        "--lanes", "front", "back",
        "--host-palette", str(host_palette),
    ])

    for lane in ("front", "back"):
        src_lane = ingest / "cyndaquil" / lane
        dst_lane = graphics / lane
        dst_lane.mkdir(parents=True, exist_ok=True)
        for png in sorted(src_lane.glob("frame_*.png")):
            shutil.copy2(png, dst_lane / png.name)
        shutil.copy2(src_lane / "manifest.json", dst_lane / "manifest.json")

    generated_c = src / "showdown_cyndaquil_idle.c"
    run([
        sys.executable, str(framework / "tools" / "emit_soulgold_showdown_s1_c.py"),
        "--ingest-root", str(ingest),
        "--species", "cyndaquil",
        "--asset-root", "graphics/showdown/cyndaquil",
        "--output", str(generated_c),
    ])

    summary = json.loads((ingest / "summary.json").read_text(encoding="utf-8"))
    summary["soulgold_revision"] = SOULGOLD_REV
    summary["species"] = "Cyndaquil"
    summary["s1_palette_policy"] = "remap_to_existing_soulgold_cyndaquil_palette"
    summary["runtime_scope"] = "front/back idle loop; move-selection ownership only"
    (out / "SHOWDOWN_S1_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared Showdown S1 staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
