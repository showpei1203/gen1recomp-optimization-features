#!/usr/bin/env python3
"""G2 wrapper around pmd_gba_converter with single-row action support.

SpriteCollab contains both eight-direction sheets and actions whose one row is
shared by every direction. G1 intentionally proved only the classic 8-row Walk
path; this G2 wrapper broadens source-layout support without changing the sealed
G1 converter behavior.
"""

from __future__ import annotations

import pmd_gba_converter as base

_original_crop = base.crop_direction_frame


def crop_direction_frame(sheet, action, direction, frame_index):
    if direction not in base.DIRECTION_TO_ROW:
        raise ValueError(f"Unknown direction {direction}; use one of {base.DIRECTIONS}")
    if frame_index < 0 or frame_index >= action.frame_count:
        raise IndexError(frame_index)

    expected_w = action.frame_width * action.frame_count
    if sheet.width < expected_w:
        raise ValueError(
            f"{action.source_action} sheet is {sheet.size}, expected width at least {expected_w}"
        )

    # PMD SpriteCollab permits non-directional actions stored as exactly one
    # frame-height row. That row is intentionally reused for every battle side.
    if sheet.height == action.frame_height:
        x0 = frame_index * action.frame_width
        return sheet.crop((x0, 0, x0 + action.frame_width, action.frame_height))

    return _original_crop(sheet, action, direction, frame_index)


base.crop_direction_frame = crop_direction_frame

if __name__ == "__main__":
    raise SystemExit(base.main())
