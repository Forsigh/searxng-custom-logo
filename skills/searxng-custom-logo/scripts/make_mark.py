#!/usr/bin/env python3
"""Render a glyph or short word as an SVG mark plus PNG fallbacks.

Transparent background by default. Pass --ink-light and the SVG embeds a
prefers-color-scheme switch so a single file reads on both light and dark browser
chrome, with the dark-chrome ink as the default (so a browser that ignores the
media query still renders correctly on dark chrome).

    # a favicon mark, theme-aware, with the usual PNG fallbacks
    python make_mark.py --font Lexend.ttf --weight 700 --text M --size 92 \
        --out-dir out --png 64,192,512 --name m-icon

    # a wordmark, single ink, no switch
    python make_mark.py --font Michroma.ttf --text BRAND --size 900:170 \
        --ink '#f4f7fa' --out-dir out --name wordmark

Requires fontTools, Pillow and numpy. Ships no fonts: pass your own, under its
licence. Variable fonts are pinned to --weight so the SVG outline, the PNGs and
whatever you preview all render the same weight.
"""
import argparse
import pathlib
import tempfile

import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont


def parse_size(raw):
    """'92' -> (92, 92);  '900:170' -> (900, 170)."""
    if ":" in raw:
        w, h = raw.split(":", 1)
        return int(w), int(h)
    return int(raw), int(raw)


def load_font(path, weight):
    tt = TTFont(str(path))
    if weight is not None and "fvar" in tt:
        if any(a.axisTag == "wght" for a in tt["fvar"].axes):
            instantiateVariableFont(tt, {"wght": weight}, inplace=True)
    return tt

def static_copy(tt, out_dir):
    """Materialise the (possibly instanced) font so Pillow can render it too."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="mark-")) / "static.ttf"
    tt.save(str(tmp))
    return tmp


def layout(tt, text):
    """Per-glyph placement plus the overall ink box, in font units."""
    gs = tt.getGlyphSet()
    cmap = tt.getBestCmap()
    hmtx = tt["hmtx"]
    placed, boxes, x = [], [], 0
    for ch in text:
        gn = cmap.get(ord(ch))
        if gn is None:
            continue
        bp = BoundsPen(gs)
        gs[gn].draw(bp)
        if bp.bounds:
            x0, y0, x1, y1 = bp.bounds
            boxes.append((x + x0, y0, x + x1, y1))
        adv = hmtx[gn][0] if gn in hmtx.metrics else tt["head"].unitsPerEm
        placed.append((gn, x))
        x += adv
    if not boxes:
        raise SystemExit("no drawable glyphs in %r" % text)
    ink = (min(b[0] for b in boxes), min(b[1] for b in boxes),
           max(b[2] for b in boxes), max(b[3] for b in boxes))
    return placed, ink


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", required=True, type=pathlib.Path)
    ap.add_argument("--weight", type=float, default=None, help="pin a variable font to this weight")
    ap.add_argument("--text", default="M")
    ap.add_argument("--name", default="mark")
    ap.add_argument("--size", default="92", help="canvas, e.g. 92 or 900:170 (w:h)")
    ap.add_argument("--fit", type=float, default=0.88,
                    help="fraction of the canvas the ink may fill, per axis (default 0.88)")
    ap.add_argument("--ink", default="#f4f7fa", help="ink for dark chrome / no switch")
    ap.add_argument("--ink-light", default=None,
                    help="ink for prefers-color-scheme: light; supplying it enables the switch")
    ap.add_argument("--out-dir", type=pathlib.Path, default=pathlib.Path("."))
    ap.add_argument("--png", default="", help="comma-separated PNG sizes, e.g. 64,192,512")
    a = ap.parse_args()

    W, H = parse_size(a.size)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    tt = load_font(a.font, a.weight)
    gs = tt.getGlyphSet()
    placed, (xmin, ymin, xmax, ymax) = layout(tt, a.text)
    iw, ih = xmax - xmin, ymax - ymin

    # fit BOTH axes: a wide display face binds on width, a near-square one on height
    scale = min((W * a.fit) / iw, (H * a.fit) / ih)
    bound_by = "width" if (W * a.fit) / iw < (H * a.fit) / ih else "height"
    tx = W / 2 - scale * (xmin + xmax) / 2
    ty = H / 2 + scale * (ymin + ymax) / 2   # fontTools is y-up, SVG is y-down

    paths = []
    for gn, off in placed:
        pen = SVGPathPen(gs)
        gs[gn].draw(pen)
        d = pen.getCommands()
        if d:
            paths.append('    <path d="%s"%s/>' % (d, ' transform="translate(%d,0)"' % off if off else ""))

    if a.ink_light:
        style = ('  <style>\n'
                 '    path { fill: %s; }\n'
                 '    @media (prefers-color-scheme: light) { path { fill: %s; } }\n'
                 '  </style>\n' % (a.ink, a.ink_light))
    else:
        style = ""
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d" role="img" aria-label="%s">\n'
           '  <title>%s</title>\n%s'
           '  <g transform="translate(%.3f,%.3f) scale(%.6f,%.6f)"%s>\n%s\n  </g>\n</svg>\n'
           % (W, H, W, H, a.text, a.text, style, tx, ty, scale, -scale,
              ' fill="%s"' % a.ink if not a.ink_light else "", "\n".join(paths)))
    svg_path = a.out_dir / (a.name + ".svg")
    # newline="\n": text mode would expand to CRLF on Windows, so the same command
    # would produce a different file for a Linux consumer
    svg_path.write_text(svg, encoding="utf-8", newline="\n")

    print("%s -> %s" % (a.text, svg_path))
    print("  canvas %dx%d, ink %.1fx%.1f px = %.0f%% x %.0f%% (bound by %s)"
          % (W, H, iw * scale, ih * scale, 100 * iw * scale / W, 100 * ih * scale / H, bound_by))
    print("  ink %s%s" % (a.ink, " + %s under prefers-color-scheme: light" % a.ink_light if a.ink_light else ""))

    if a.png:
        static = static_copy(tt, a.out_dir)
        upm = tt["head"].unitsPerEm
        for size in [int(s) for s in a.png.split(",") if s.strip()]:
            ss = 8
            S = size * ss
            sc = min((size * a.fit) / iw, (size * a.fit) / ih)
            f = ImageFont.truetype(str(static), int(round(upm * sc * ss)))
            img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            bb = f.getbbox(a.text)
            d.text(((S - (bb[2] - bb[0])) / 2 - bb[0], (S - (bb[3] - bb[1])) / 2 - bb[1]),
                   a.text, font=f, fill=a.ink)
            out = a.out_dir / ("%s-%d.png" % (a.name, size))
            img.resize((size, size), Image.LANCZOS).save(out)
            arr = np.array(Image.open(out))
            assert arr[0, 0, 3] == 0, "%s: corner is not transparent" % out.name
            assert arr[:, :, 3].max() > 200, "%s: no opaque glyph" % out.name
            print("  %s (%dx%d, transparent)" % (out.name, size, size))


if __name__ == "__main__":
    main()
