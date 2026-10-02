#!/usr/bin/env python3
"""Contact sheet of candidate typefaces for a one-letter mark, at real render sizes.

Every candidate is fitted to the same ink fraction, so what you are comparing is the
letterform and its weight, not accidental size differences. Sizes shown are the sizes
that matter: a favicon is judged at 16px, not at the poster size you design it at.

    python font_contact_sheet.py --spec Lexend.ttf:700 --spec Audiowide.ttf \
        --spec ZenDots.ttf --sizes 16,32,48,64 --out candidates.png

Requires fontTools, Pillow. Ships no fonts: pass your own, under its licence.
Variable fonts are instanced to the weight in the spec so the sheet shows the real weight.
"""
import argparse
import pathlib
import tempfile

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont


class Candidate:
    def __init__(self, spec, font_dirs):
        name, _, weight = spec.partition(":")
        path = None
        for d in font_dirs:
            cand = d / name
            if cand.exists():
                path = cand
                break
        if path is None:
            raise SystemExit("font not found: %s (searched %s)"
                             % (name, ", ".join(str(d) for d in font_dirs)))
        self.label = path.stem.replace("-", " ")
        self.weight = float(weight) if weight else None
        if self.weight:
            self.label += " %g" % self.weight
        tt = TTFont(str(path))
        if self.weight and "fvar" in tt and any(a.axisTag == "wght" for a in tt["fvar"].axes):
            instantiateVariableFont(tt, {"wght": self.weight}, inplace=True)
        self.tt = tt
        self.path = pathlib.Path(tempfile.mkdtemp(prefix="sheet-")) / (path.stem + ".ttf")
        tt.save(str(self.path))
        gs = tt.getGlyphSet()
        self.glyph = tt.getBestCmap()[ord(args_glyph)]
        bp = BoundsPen(gs)
        gs[self.glyph].draw(bp)
        x0, y0, x1, y1 = bp.bounds
        self.iw, self.ih = x1 - x0, y1 - y0
        self.upm = tt["head"].unitsPerEm


def render(canvas, cand, size, xy, ink, fit):
    ss = 8
    S = size * ss
    sc = min((S * fit) / cand.iw, (S * fit) / cand.ih)
    f = ImageFont.truetype(str(cand.path), int(round(cand.upm * sc)))
    tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    bb = f.getbbox(args_glyph)
    d.text(((S - (bb[2] - bb[0])) / 2 - bb[0], (S - (bb[3] - bb[1])) / 2 - bb[1]),
           args_glyph, font=f, fill=ink + (255,))
    canvas.paste(tile.resize((size, size), Image.LANCZOS), xy, tile.resize((size, size), Image.LANCZOS))


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--spec", action="append", required=True,
                help="FontFile.ttf[:weight], repeat for each candidate")
ap.add_argument("--font-dir", action="append", default=None,
                help="directory to search for font files (repeatable; default: the cwd)")
ap.add_argument("--glyph", default="M")
ap.add_argument("--sizes", default="16,32,48,64")
ap.add_argument("--ink", default="#f4f7fa", help="glyph colour")
ap.add_argument("--bg", default="#202124", help="background, i.e. the chrome you are testing against")
ap.add_argument("--fit", type=float, default=0.88)
ap.add_argument("--out", default="candidates.png")
a = ap.parse_args()
args_glyph = a.glyph


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


dirs = [pathlib.Path(d) for d in (a.font_dir or ["."])]
sizes = [int(s) for s in a.sizes.split(",")]
cands = [Candidate(s, dirs) for s in a.spec]

LBL_W, COL_W, HDR_H, ROW_H = 220, 96, 78, 84
W = LBL_W + COL_W * len(sizes) + 30
H = HDR_H + ROW_H * len(cands) + 24
sheet = Image.new("RGB", (W, H), hex_rgb(a.bg))
dr = ImageDraw.Draw(sheet)
note_font = ImageFont.truetype(str(cands[0].path), 15)
head_font = ImageFont.truetype(str(cands[0].path), 17)
dr.text((20, 18), "%s candidates at real render size" % a.glyph, font=head_font, fill=hex_rgb(a.ink))
for i, s in enumerate(sizes):
    dr.text((LBL_W + COL_W * i + 20, 50), "%dpx" % s, font=note_font, fill=(150, 158, 170))

for r, c in enumerate(cands):
    y = HDR_H + r * ROW_H
    if r % 2:
        dr.rectangle([0, y, W, y + ROW_H], fill=tuple(min(255, v + 6) for v in hex_rgb(a.bg)))
    dr.text((20, y + ROW_H // 2 - 9), c.label, font=note_font, fill=(225, 229, 234))
    for i, s in enumerate(sizes):
        render(sheet, c, s, (LBL_W + COL_W * i + (COL_W - s) // 2, y + (ROW_H - s) // 2), hex_rgb(a.ink), a.fit)
    print("  %-24s ink ratio %.2f" % (c.label, c.iw / c.ih))

sheet.save(a.out)
print("\nsheet: %s (%dx%d)" % (a.out, W, H))
print("judge at the smallest size shown, not the largest.")
