#!/usr/bin/env bash
set -euo pipefail

# Reproducible Phase G0 capture for Pokémon SoulGold PMD Animated Prototype.
# This script records source/toolchain/build identity. Emulator visual acceptance
# remains a separate human/runtime gate and is never auto-promoted by this file.

SOULGOLD_REPO="${SOULGOLD_REPO:-https://github.com/Eemeliri/soulgold.git}"
SOULGOLD_COMMIT="${SOULGOLD_COMMIT:-b5122bdf188943862c13abe4938e88b7bb3c5c4a}"
WORK_ROOT="${WORK_ROOT:-$PWD/.pmd_soulgold_baseline}"
SRC_DIR="$WORK_ROOT/soulgold"
EVIDENCE_DIR="${EVIDENCE_DIR:-$PWD/evidence/soulgold_g0_baseline}"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 2)}"
BUILD_COMMAND="make -j${JOBS}"

mkdir -p "$WORK_ROOT" "$EVIDENCE_DIR"

if [[ ! -d "$SRC_DIR/.git" ]]; then
  git clone "$SOULGOLD_REPO" "$SRC_DIR"
fi

cd "$SRC_DIR"
git fetch --tags --prune origin
git reset --hard
git clean -ffd
git checkout --detach "$SOULGOLD_COMMIT"

ACTUAL_COMMIT="$(git rev-parse HEAD)"
if [[ "$ACTUAL_COMMIT" != "$SOULGOLD_COMMIT" ]]; then
  echo "ERROR: expected $SOULGOLD_COMMIT, got $ACTUAL_COMMIT" >&2
  exit 2
fi

{
  echo "git: $(git --version 2>&1)"
  echo "make: $(make --version 2>&1 | head -n 1)"
  echo "python: $(python3 --version 2>&1 || true)"
  echo "arm-none-eabi-gcc: $(arm-none-eabi-gcc --version 2>&1 | head -n 1 || true)"
  echo "arm-none-eabi-as: $(arm-none-eabi-as --version 2>&1 | head -n 1 || true)"
  echo "arm-none-eabi-ld: $(arm-none-eabi-ld --version 2>&1 | head -n 1 || true)"
  echo "uname: $(uname -a 2>&1)"
} > "$EVIDENCE_DIR/TOOLCHAIN.txt"

echo "$BUILD_COMMAND" > "$EVIDENCE_DIR/BUILD_COMMAND.txt"

# Clean compile. Do not turn a stale ROM into a fake baseline PASS.
make clean > "$EVIDENCE_DIR/MAKE_CLEAN.log" 2>&1 || true
set +e
bash -lc "$BUILD_COMMAND" > "$EVIDENCE_DIR/MAKE_BUILD.log" 2>&1
BUILD_RC=$?
set -e

echo "$BUILD_RC" > "$EVIDENCE_DIR/BUILD_EXIT_CODE.txt"
if [[ "$BUILD_RC" -ne 0 ]]; then
  cat > "$EVIDENCE_DIR/PMD_ANIMATED_BASELINE.md" <<EOF
# Pokémon SoulGold PMD Animated Baseline

Status: **BUILD FAIL**

- Source repo: \`$SOULGOLD_REPO\`
- Pinned commit: \`$SOULGOLD_COMMIT\`
- Actual commit: \`$ACTUAL_COMMIT\`
- Build command: \`$BUILD_COMMAND\`
- Exit code: \`$BUILD_RC\`

The build log is \`MAKE_BUILD.log\`. No ROM identity is recorded because a failed compile is not a baseline.
EOF
  echo "BUILD FAIL. See $EVIDENCE_DIR/MAKE_BUILD.log" >&2
  exit "$BUILD_RC"
fi

# Prefer the documented expansion output; otherwise accept exactly one root GBA.
ROM_PATH="${ROM_PATH:-pokeemerald.gba}"
if [[ ! -f "$ROM_PATH" ]]; then
  mapfile -t gba_files < <(find . -maxdepth 1 -type f -name '*.gba' -printf '%P\n' | sort)
  if [[ "${#gba_files[@]}" -ne 1 ]]; then
    printf 'ERROR: build succeeded but ROM could not be uniquely identified. Found: %s\n' "${gba_files[*]:-none}" >&2
    exit 3
  fi
  ROM_PATH="${gba_files[0]}"
fi

ROM_SIZE="$(stat -c '%s' "$ROM_PATH" 2>/dev/null || stat -f '%z' "$ROM_PATH")"
ROM_SHA256="$(sha256sum "$ROM_PATH" | awk '{print $1}')"
ROM_CRC32="$(python3 - "$ROM_PATH" <<'PY'
import sys, zlib
p = sys.argv[1]
crc = 0
with open(p, 'rb') as f:
    for block in iter(lambda: f.read(1024 * 1024), b''):
        crc = zlib.crc32(block, crc)
print(f"{crc & 0xffffffff:08X}")
PY
)"

cp -f "$ROM_PATH" "$EVIDENCE_DIR/$(basename "$ROM_PATH")"
printf '%s  %s\n' "$ROM_SHA256" "$(basename "$ROM_PATH")" > "$EVIDENCE_DIR/SHA256.txt"
printf '%s  %s\n' "$ROM_CRC32" "$(basename "$ROM_PATH")" > "$EVIDENCE_DIR/CRC32.txt"
printf '%s\n' "$ROM_SIZE" > "$EVIDENCE_DIR/ROM_SIZE_BYTES.txt"

git status --porcelain=v1 > "$EVIDENCE_DIR/GIT_STATUS.txt"

git show -s --format='commit=%H%ncommit_date=%cI%nsubject=%s' HEAD > "$EVIDENCE_DIR/SOURCE_COMMIT.txt"

cat > "$EVIDENCE_DIR/PMD_ANIMATED_BASELINE.md" <<EOF
# Pokémon SoulGold PMD Animated Baseline

Status: **BUILD PASS / EMULATOR ACCEPTANCE PENDING**

## Source

- Source repo: \`$SOULGOLD_REPO\`
- Baseline commit: \`$ACTUAL_COMMIT\`
- Build command: \`$BUILD_COMMAND\`
- Working tree after build: see \`GIT_STATUS.txt\`

## ROM identity

- ROM: \`$(basename "$ROM_PATH")\`
- Size: \`$ROM_SIZE\` bytes
- SHA-256: \`$ROM_SHA256\`
- CRC32: \`$ROM_CRC32\`

## Toolchain

See \`TOOLCHAIN.txt\`.

## Runtime acceptance

- mGBA desktop boot: **PENDING**
- RetroArch + mGBA boot: **PENDING**
- AYN THOR runtime: **PENDING**

A successful compile does not promote runtime or visual status.

## Known issues

None are inferred from a clean compile alone. Runtime findings must be recorded from actual emulator evidence.
EOF

echo "Baseline build captured: $EVIDENCE_DIR"
echo "ROM: $ROM_PATH"
echo "SHA256: $ROM_SHA256"
echo "CRC32: $ROM_CRC32"
