#!/usr/bin/env python3
"""Prepare SoulGold G3R5B runtime-corrected body + centered authentic PMD shadow assets."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
ACTIONS = ("Idle", "Walk", "Nod", "Rotate")
TARGETS = (
    {"species": "Cyndaquil", "slug": "cyndaquil", "dex": "155", "spritecollab_id": "0155", "variant": "player", "direction": "UpRight"},
    {"species": "Marill", "slug": "marill", "dex": "183", "spritecollab_id": "0183", "variant": "opponent", "direction": "DownLeft"},
)


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def copy_variant_assets(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for action in ACTIONS:
        shutil.copytree(src / action.lower(), dst / action.lower())
    shutil.copy2(src / "manifest.ir.json", dst / "manifest.ir.json")


def center_shadow_x(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"const s8 (gPmd\w+GroundShadowXOffset) = (-?\d+);", text)
    if not m:
        raise SystemExit(f"Shadow X offset symbol not found: {path}")
    authored = int(m.group(2))
    text = text[:m.start()] + f"const s8 {m.group(1)} = 0;" + text[m.end():]
    text = text.replace(
        "/* Palette index 0 is transparent; index 1 uses SoulGold's loaded shadow palette. */",
        "/* Palette index 0 is transparent; index 1 uses SoulGold's loaded shadow palette. */\n"
        "/* G3R5B battle policy: authentic PMD mask, centered on battler base X. */",
        1,
    )
    path.write_text(text, encoding="utf-8")
    return authored


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    framework = args.framework_root.resolve()
    spritecollab = args.spritecollab.resolve()
    soulgold = args.soulgold.resolve()
    out = args.output.resolve()
    base_out = out / "g3r5_base"
    staging = out / "staging"
    work = out / "work"

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # Reuse sealed G3R5 only for authentic PMDCollab shadow extraction.
    run([
        sys.executable, str(framework / "tools" / "prepare_soulgold_g3r5_assets.py"),
        "--framework-root", str(framework),
        "--spritecollab", str(spritecollab),
        "--soulgold", str(soulgold),
        "--output", str(base_out),
    ])
    shutil.copytree(base_out / "staging", staging)
    work.mkdir(parents=True)
    base_summary = json.loads((base_out / "G3R5_ASSET_SUMMARY.json").read_text(encoding="utf-8"))

    summary = {
        "phase": "G3R5B_RUNTIME_OVERRIDE_CENTERED_PMD_SHADOW",
        "parent": "G3R5_AUTHENTIC_SHADOW_RUNTIME_PARTIAL_FAIL",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "body_grounding_policy": "G3R4B_ZERO_PLUS_RUNTIME_ACCEPTANCE_OVERRIDE",
        "shadow_art_policy": "AUTHENTIC_PMDCOLLAB_IDLE0_MASK",
        "shadow_x_policy": "CENTER_ON_SOULGOLD_BATTLER_BASE_X",
        "shadow_y_policy": "PMD_AUTHORED_IDLE0_VERTICAL_OFFSET",
        "shadow_png_may_move_body": False,
        "targets": {},
    }

    for target in TARGETS:
        key = f"{target['species']}_{target['variant']}"
        base_rec = base_summary["targets"][key]
        anchor_x, anchor_y = base_rec["resolved_body_anchor"]
        species_dir = spritecollab / "sprite" / target["spritecollab_id"]
        variant_dir = work / f"{target['slug']}_{target['variant']}"
        host_palette = soulgold / "graphics" / "pokemon" / target["slug"] / "normal.pal"

        run([
            sys.executable, str(framework / "tools" / "convert_soulgold_g3r5b.py"),
            "--source", str(species_dir),
            "--species", target["species"],
            "--national-dex", target["dex"],
            "--actions", ",".join(ACTIONS),
            "--direction", target["direction"],
            "--anchor-x", str(anchor_x),
            "--anchor-y", str(anchor_y),
            "--source-revision", SPRITECOLLAB_REV,
            "--source-repo-path", f"sprite/{target['spritecollab_id']}",
            "--output", str(variant_dir),
            "--host-asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])
        run([
            sys.executable, str(framework / "tools" / "pmd_gba_remap_host_palette.py"),
            "--frames-root", str(variant_dir),
            "--host-palette", str(host_palette),
        ])
        run([
            sys.executable, str(framework / "tools" / "emit_soulgold_g3r5b_c.py"),
            "--ir", str(variant_dir / "manifest.ir.json"),
            "--output", str(staging / "src" / f"pmd_{target['slug']}_{target['variant']}_ambient.c"),
            "--variant", target["variant"],
            "--asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])
        copy_variant_assets(variant_dir, staging / "graphics" / "pmd" / target["slug"] / target["variant"])

        shadow_c = staging / "src" / f"pmd_{target['slug']}_{target['variant']}_shadow.c"
        authored_x = center_shadow_x(shadow_c)
        manifest = json.loads((variant_dir / "manifest.ir.json").read_text(encoding="utf-8"))
        corrections = manifest["grounding"]["presentation_corrections_y"]

        summary["targets"][key] = {
            "species": target["species"],
            "variant": target["variant"],
            "direction": target["direction"],
            "resolved_body_anchor": [anchor_x, anchor_y],
            "body_ground_correction_range": manifest["g3r5b_body_ground_correction_range"],
            "body_ground_corrections": corrections,
            "idle_corrections": corrections["Idle"],
            "runtime_acceptance_overrides": manifest["grounding"]["runtime_acceptance_overrides"],
            "pmd_authored_idle0_shadow_x_offset": authored_x,
            "battle_shadow_x_offset": 0,
            "battle_shadow_y_offset": base_rec["shadow_asset"]["body_sprite_base_offset"][1],
            "shadow_asset": base_rec["shadow_asset"],
        }

    cy = summary["targets"]["Cyndaquil_player"]
    if cy["idle_corrections"] != [0, -1]:
        raise SystemExit(f"G3R5B requires exact Cyndaquil Idle correction [0,-1], got {cy['idle_corrections']}")
    for key, rec in summary["targets"].items():
        if key != "Cyndaquil_player":
            all_values = [v for vals in rec["body_ground_corrections"].values() for v in vals]
            if any(v != 0 for v in all_values):
                raise SystemExit(f"Non-target body offset changed in G3R5B: {key} {rec['body_ground_corrections']}")
    if cy["battle_shadow_x_offset"] != 0:
        raise SystemExit("Player shadow must be centered on battler base X")

    (out / "G3R5B_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared SoulGold G3R5B staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
