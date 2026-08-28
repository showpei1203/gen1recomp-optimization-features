#!/usr/bin/env python3
"""Prepare SoulGold G3R2 Cyndaquil grounded PMD ambient assets.

G3R2 preserves raw PMD tile-space inside every action and uses one action-level
shadow ground translation. Per-frame green body-center translation is forbidden.
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
BANNED = ("LookUp", "DeepBreath", "Sit")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def require_revision(repo: Path, expected: str, label: str) -> None:
    actual = git_head(repo)
    if actual != expected:
        raise SystemExit(f"{label} revision mismatch: expected {expected}, got {actual}")


def shadow_alpha_delta(shadowed: Path, body_only: Path) -> int:
    a = Image.open(shadowed).convert("RGBA")
    b = Image.open(body_only).convert("RGBA")
    if a.size != b.size:
        raise SystemExit(f"Shadow audit size mismatch: {a.size} != {b.size}")
    return sum(
        1
        for y in range(a.height)
        for x in range(a.width)
        if a.getpixel((x, y))[3] > 0 and b.getpixel((x, y))[3] == 0
    )


def copy_variant_assets(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for action in ACTIONS:
        shutil.copytree(src / action.lower(), dst / action.lower())
    shutil.copy2(src / "manifest.ir.json", dst / "manifest.ir.json")


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

    species = spritecollab / "sprite" / "0155"
    host_palette = soulgold / "graphics" / "pokemon" / "cyndaquil" / "normal.pal"
    if out.exists():
        shutil.rmtree(out)
    work = out / "work"
    staging = out / "staging"
    work.mkdir(parents=True)
    (staging / "src").mkdir(parents=True)
    (staging / "graphics" / "pmd" / "cyndaquil").mkdir(parents=True)

    converter = framework / "tools" / "convert_soulgold_g3r2.py"
    remapper = framework / "tools" / "pmd_gba_remap_host_palette.py"
    emitter = framework / "tools" / "emit_soulgold_g3_c.py"
    action_arg = ",".join(ACTIONS)

    summary = {
        "phase": "G3R2_POST_NATIVE_LOAD_GROUNDED_SHADOW",
        "species": "Cyndaquil",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "actions": list(ACTIONS),
        "banned_from_ambient": list(BANNED),
        "grounding_policy": "PMD raw tile-space; one shadow-ground translation per action; no per-frame body-center positioning",
        "variants": {},
    }

    for variant, direction in (("player", "UpRight"), ("opponent", "DownLeft")):
        variant_dir = work / variant
        body_dir = work / f"{variant}_body_only"
        common = [
            "--source", str(species), "--species", "Cyndaquil", "--national-dex", "155",
            "--actions", action_arg, "--direction", direction,
            "--source-revision", SPRITECOLLAB_REV, "--source-repo-path", "sprite/0155",
        ]
        run([sys.executable, str(converter), *common, "--output", str(variant_dir),
             "--host-asset-root", f"graphics/pmd/cyndaquil/{variant}"])
        run([sys.executable, str(converter), *common, "--no-shadow", "--output", str(body_dir),
             "--host-asset-root", f"graphics/pmd/cyndaquil/{variant}_body_only"])

        manifest = json.loads((variant_dir / "manifest.ir.json").read_text(encoding="utf-8"))
        grounding = manifest.get("grounding", {})
        if grounding.get("policy") != "PMD_TILE_SPACE_ACTION_CONSTANT_SHADOW_GROUND_ANCHOR":
            raise SystemExit(f"G3R2 grounding policy missing for {variant}")
        if grounding.get("body_center_controls_translation") is not False:
            raise SystemExit(f"Per-frame body-center positioning still active for {variant}")
        if manifest.get("shadow", {}).get("shadow_size") != 1:
            raise SystemExit(f"Unexpected Cyndaquil ShadowSize for {variant}")

        action_summary = {}
        for action in ACTIONS:
            frames = manifest["actions"][action]["frames"]
            translations = {(int(f["paste_x"]), int(f["paste_y"])) for f in frames}
            if len(translations) != 1:
                raise SystemExit(f"G3R2 drift gate FAIL {variant}/{action}: translations={sorted(translations)}")
            expected = grounding["actions"][action]
            only = next(iter(translations))
            if only != (int(expected["paste_x"]), int(expected["paste_y"])):
                raise SystemExit(f"Ground metadata mismatch {variant}/{action}")

            shadow_counts = []
            for frame in frames:
                idx = int(frame["index"])
                shadowed = variant_dir / action.lower() / f"frame_{idx:02d}.png"
                body_only = body_dir / action.lower() / f"frame_{idx:02d}.png"
                extra = shadow_alpha_delta(shadowed, body_only)
                if extra <= 0:
                    raise SystemExit(f"Shadow pixel gate FAIL {variant}/{action}/frame_{idx:02d}")
                shadow_counts.append(extra)

            action_summary[action] = {
                "frame_count": len(frames),
                "constant_translation": list(only),
                "shadow_extra_opaque_pixels": shadow_counts,
            }

        run([sys.executable, str(remapper), "--frames-root", str(variant_dir), "--host-palette", str(host_palette)])
        generated = staging / "src" / f"pmd_cyndaquil_{variant}_ambient.c"
        run([sys.executable, str(emitter), "--ir", str(variant_dir / "manifest.ir.json"),
             "--output", str(generated), "--variant", variant,
             "--asset-root", f"graphics/pmd/cyndaquil/{variant}"])
        copy_variant_assets(variant_dir, staging / "graphics" / "pmd" / "cyndaquil" / variant)

        summary["variants"][variant] = {
            "direction": direction,
            "grounding": grounding,
            "actions": action_summary,
        }

    (out / "G3R2_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared G3R2 grounded staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
