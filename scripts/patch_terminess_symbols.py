#!/usr/bin/env python3
"""Add pixel-art glyphs for symbols that Terminess lacks.

cool-retro-term renders Terminess at 12 px. Symbols missing from the font
(the Claude Code spinner, ⏺, ◐◑◒◓, ⚠, ...) fall back to a system font, which
looks terrible without anti-aliasing. This script draws them as pixel squares
on the same 6x12 grid, so they stay crisp and match the rest of the font.

Usage:  pip install fonttools && python3 scripts/patch_terminess_symbols.py

Rewrites app/qml/fonts/terminus/TerminessNerdFontMono-Regular.ttf in place.
Running it twice is harmless: glyphs that already exist are skipped.
Designs for most symbols are borrowed from Cozette (MIT licensed).
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen

FONT = os.path.join(os.path.dirname(__file__), "..", "app", "qml", "fonts",
                    "terminus", "TerminessNerdFontMono-Regular.ttf")
PIXELS_PER_EM = 12          # size cool-retro-term renders Terminess at
ADVANCE = 500               # every Terminess glyph is half an em wide

# codepoint -> (rows above the baseline of the bottom row, bitmap top..bottom)
# Each bitmap is 6 columns wide; '#' is a filled pixel.
BITMAPS = {
    0x2722: (0, [  # ✢ four teardrop-spoked asterisk
        "...#..",
        "...#..",
        "...#..",
        "######",
        "...#..",
        "...#..",
        "...#..",
    ]),
    0x2733: (0, [  # ✳ eight spoked asterisk (Claude Code spinner)
        "...#..",
        ".#.#.#",
        "..###.",
        "######",
        "..###.",
        ".#.#.#",
        "...#..",
    ]),
    0x2736: (0, [  # ✶ six pointed black star
        "...#..",
        ".#.#.#",
        ".#####",
        "..###.",
        ".#####",
        ".#.#.#",
        "...#..",
    ]),
    0x273B: (0, [  # ✻ teardrop-spoked asterisk
        "..#.#.",
        "...#..",
        ".#####",
        "..###.",
        ".#####",
        "...#..",
        "..#.#.",
    ]),
    0x273D: (0, [  # ✽ heavy teardrop-spoked pinwheel asterisk
        ".#.#.#",
        "..###.",
        ".#####",
        "######",
        ".#####",
        "..###.",
        ".#.#.#",
    ]),
    0x23FA: (1, [  # ⏺ black circle for record (Claude Code message bullet)
        "..###.",
        ".#####",
        ".#####",
        ".#####",
        "..###.",
    ]),
    0x25EF: (0, [  # ◯ large circle
        "..##..",
        ".#..#.",
        "#....#",
        "#....#",
        "#....#",
        "#....#",
        ".#..#.",
        "..##..",
    ]),
    0x25D0: (0, [  # ◐ circle with left half black
        "..###.",
        ".###.#",
        "####..",
        "####..",
        "####..",
        ".###.#",
        "..###.",
    ]),
    0x25D1: (0, [  # ◑ circle with right half black
        "..###.",
        ".#.###",
        "#..###",
        "#..###",
        "#..###",
        ".#.###",
        "..###.",
    ]),
    0x25D2: (0, [  # ◒ circle with lower half black
        "..###.",
        ".#...#",
        "#.....",
        "######",
        "######",
        ".#####",
        "..###.",
    ]),
    0x25D3: (0, [  # ◓ circle with upper half black
        "..###.",
        ".#####",
        "######",
        "######",
        "#.....",
        ".#...#",
        "..###.",
    ]),
    0x26A0: (0, [  # ⚠ warning sign
        "...#..",
        "..###.",
        "..#.#.",
        ".##.##",
        ".#####",
        "###.##",
        "######",
    ]),
    0x21E7: (0, [  # ⇧ upwards white arrow (shift)
        "...#..",
        "..###.",
        ".##.##",
        "..#.#.",
        "..#.#.",
        "..#.#.",
        "..###.",
    ]),
    0x23CE: (1, [  # ⏎ return symbol
        ".....#",
        ".....#",
        ".....#",
        "..#..#",
        ".#####",
        "..#...",
    ]),
    0x2318: (0, [  # ⌘ place of interest sign (command)
        ".#...#",
        "#.#.#.",
        ".#####",
        "..#.#.",
        ".#####",
        "#.#.#.",
        ".#...#",
    ]),
    0x25B8: (1, [  # ▸ black right-pointing small triangle
        "..#...",
        "..##..",
        "..###.",
        "..##..",
        "..#...",
    ]),
    0x25AA: (1, [  # ▪ black small square
        ".#####",
        ".#####",
        ".#####",
        ".#####",
        ".#####",
    ]),
    0x22EF: (3, [  # ⋯ midline horizontal ellipsis
        ".#.#.#",
    ]),
}

# codepoint -> existing glyph that looks the same
ALIASES = {
    0x23BF: 0x2514,  # ⎿ (Claude Code tool-result connector) -> └
}


def build_glyph(font, bottom_row, rows):
    unit = font["head"].unitsPerEm / PIXELS_PER_EM
    pen = TTGlyphPen(font.getGlyphSet())
    height = len(rows)
    for i, row in enumerate(rows):
        y0 = (bottom_row + height - 1 - i) * unit
        y1 = y0 + unit
        # one rectangle per run of filled pixels, drawn clockwise
        col = 0
        while col < len(row):
            if row[col] != "#":
                col += 1
                continue
            start = col
            while col < len(row) and row[col] == "#":
                col += 1
            x0, x1 = start * unit, col * unit
            pen.moveTo((round(x0), round(y0)))
            pen.lineTo((round(x0), round(y1)))
            pen.lineTo((round(x1), round(y1)))
            pen.lineTo((round(x1), round(y0)))
            pen.closePath()
    return pen.glyph()


def add_to_cmap(font, codepoint, glyph_name):
    for table in font["cmap"].tables:
        if table.isUnicode():
            table.cmap[codepoint] = glyph_name


def main():
    font = TTFont(FONT)
    cmap = font.getBestCmap()
    order = font.getGlyphOrder()
    added = []

    for codepoint, (bottom_row, rows) in BITMAPS.items():
        if codepoint in cmap:
            continue
        name = "uni%04X" % codepoint
        glyph = build_glyph(font, bottom_row, rows)
        order.append(name)
        font["glyf"][name] = glyph
        font["hmtx"][name] = (ADVANCE, glyph.xMin if hasattr(glyph, "xMin") else 0)
        add_to_cmap(font, codepoint, name)
        added.append(chr(codepoint))

    for codepoint, target in ALIASES.items():
        if codepoint in cmap or target not in cmap:
            continue
        add_to_cmap(font, codepoint, cmap[target])
        added.append(chr(codepoint))

    if not added:
        print("nothing to do, all symbols present")
        return
    font.setGlyphOrder(order)
    font.save(FONT)
    print("added", " ".join(added))


if __name__ == "__main__":
    main()
