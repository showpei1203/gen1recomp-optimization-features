#!/usr/bin/env python3
"""Prepare Sprigatito-back + Marill-front Showdown assets for SoulGold S1B.

S1B is a deterministic runtime-test candidate. The player's saved lead remains
untouched; only a temporary Marill enemy is created by the B-button harness.
Each Showdown lane is remapped to that species' existing SoulGold palette.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
TARGETS = (
    ("sprigatito", "back"),
    ("marill", "front"),
)


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def require_revision(repo: Path) -> None:
    actual = git_head(repo)
    if actual != SOULGOLD_REV:
        raise SystemExit(f"SoulGold revision mismatch: expected {SOULGOLD_REV}, got {actual}")


def copy_lane(ingest: Path, staging: Path, species: str, lane: str) -> None:
    src_lane = ingest / species / lane
    dst_lane = staging / "graphics" / "showdown" / species / lane
    dst_lane.mkdir(parents=True, exist_ok=True)
    for png in sorted(src_lane.glob("frame_*.png")):
        shutil.copy2(png, dst_lane / png.name)
    shutil.copy2(src_lane / "manifest.json", dst_lane / "manifest.json")


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

    if out.exists():
        shutil.rmtree(out)
    ingest = out / "ingest"
    staging = out / "staging"
    src = staging / "src"
    src.mkdir(parents=True, exist_ok=True)

    manifests: list[dict] = []
    for index, (species, lane) in enumerate(TARGETS):
        host_palette = soulgold / "graphics" / "pokemon" / species / "normal.pal"
        if not host_palette.is_file():
            raise SystemExit(f"Missing SoulGold {species} palette: {host_palette}")

        cmd = [
            sys.executable, str(framework / "tools" / "showdown_sprites_ingest.py"),
            "--zip", str(sprites_zip),
            "--output", str(ingest),
            "--species", species,
            "--lanes", lane,
            "--host-palette", str(host_palette),
        ]
        if index:
            cmd.append("--force")
        run(cmd)
        copy_lane(ingest, staging, species, lane)
        manifests.append(json.loads((ingest / species / lane / "manifest.json").read_text(encoding="utf-8")))

        generated_c = src / f"showdown_{species}_{lane}_idle.c"
        run([
            sys.executable, str(framework / "tools" / "emit_soulgold_showdown_s1_c.py"),
            "--ingest-root", str(ingest),
            "--species", species,
            "--lanes", lane,
            "--asset-root", f"graphics/showdown/{species}",
            "--output", str(generated_c),
        ])

    summary = {
        "format": "soulgold-showdown-s1b-runtime-test-v1",
        "soulgold_revision": SOULGOLD_REV,
        "targets": [
            {"species": "Sprigatito", "side": "player", "lane": "back"},
            {"species": "Marill", "side": "opponent", "lane": "front"},
        ],
        "palette_policy": "per-species existing SoulGold normal palette",
        "runtime_scope": "move-selection idle ownership + temporary overworld B-button battle harness",
        "animations": manifests,
    }
    (out / "SHOWDOWN_S1_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared Showdown S1B staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
