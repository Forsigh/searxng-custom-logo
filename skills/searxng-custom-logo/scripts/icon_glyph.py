#!/usr/bin/env python3
"""Resolve an icon name to the glyph a font actually ships, then hand it to make_mark.py.

Icon fonts park their glyphs at private-use codepoints that move between releases, so a
hardcoded codepoint breaks on the next update. These fonts also keep real glyph names in
their cmap ("magnifying-glass", "search", "rocket"), so look the icon up by name instead.

  python icon_glyph.py --font fa-solid-900.ttf --name magnifying-glass
  python icon_glyph.py --font bootstrap-icons.ttf --name search --find
  python icon_glyph.py --font bootstrap-icons.woff2 --name search --to-mark-font bootstrap-icons.ttf

Why this beats shipping SVG icons: PIL cannot rasterise SVG, but it reads any TTF/OTF. So an
icon font turns "use a real icon instead of a letter" into one flag on the existing pipeline.
woff2 needs converting first - --to-mark-font does that when brotli is installed.

Free sets that ship a usable font file, with the licence you must pass on:
  Font Awesome Free   fa-solid-900.ttf                CC BY 4.0 (icons)
  Material Symbols    MaterialSymbolsOutlined*.ttf    Apache 2.0
  Bootstrap Icons     bootstrap-icons.woff2          MIT
  Ionicons            ionicons.ttf                   MIT
  Phosphor            Phosphor.ttf                   MIT

Licence trap: an icon font's *file* may be OFL/MIT while the *pictures* carry CC BY. Font
Awesome Free is the common case - the font is SIL OFL, the icons are CC BY 4.0 and need
attribution wherever they are redistributed. Check the set's own LICENSE before shipping.
"""
import argparse
import pathlib
import sys


def load_cmap(path):
    from fontTools.ttLib import TTFont
    return TTFont(str(path), lazy=True).getBestCmap()


def to_ttf(src, dst):
    """woff2 -> ttf so PIL can open it. Needs brotli."""
    from fontTools.ttLib import TTFont
    f = TTFont(str(src))
    f.flavor = None
    f.save(str(dst))
    return dst


def main():
    ap = argparse.ArgumentParser(
        description="Resolve an icon by name from a font's own cmap, then render it as a mark.",
        epilog="Never hardcode the private-use codepoint: it moves between font releases, and a "
               "stale one renders the wrong icon with no error.\n\n"
               "  icon_glyph.py --font fa-solid-900.ttf --name magnifying-glass --render out/\n"
               "  icon_glyph.py --font bootstrap-icons.woff2 --name search --to-mark-font bi.ttf\n"
               "  icon_glyph.py --font bi.ttf --name compass --find\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", required=True, type=pathlib.Path, help="TTF/OTF, or woff2 with --to-mark-font")
    ap.add_argument("--name", help="glyph name, e.g. magnifying-glass")
    ap.add_argument("--find", action="store_true", help="list every glyph name matching --name")
    ap.add_argument("--to-mark-font", type=pathlib.Path,
                    help="convert a woff2 to this TTF path first")
    ap.add_argument("--char-only", action="store_true", help="print just the character")
    ap.add_argument("--render", metavar="OUT_DIR",
                    help="run make_mark.py with the resolved glyph, writing marks into OUT_DIR")
    ap.add_argument("--sizes", default="16,32,48,64,192", help="PNG sizes for --render")
    ap.add_argument("--ink", default="#14171c", help="mark colour for --render")
    a = ap.parse_args()

    font = a.font
    if font.suffix.lower() == ".woff2":
        if not a.to_mark_font:
            sys.exit("a woff2 cannot be read directly - pass --to-mark-font <out.ttf>")
        to_ttf(font, a.to_mark_font)
        font = a.to_mark_font
    if not font.exists():
        sys.exit("no such font: %s" % font)

    cmap = load_cmap(font)
    byname = {}
    for cp, gname in cmap.items():
        byname.setdefault(gname, cp)

    if not a.name:
        print("%d named glyphs in %s" % (len(byname), font.name))
        return

    if a.find:
        hits = sorted(n for n in byname if a.name.lower() in n.lower())
        print("\n".join("%s\tU+%04X" % (n, byname[n]) for n in hits) or "no match for %r" % a.name)
        return

    if a.name not in byname:
        near = sorted(n for n in byname if a.name.lower() in n.lower())[:12]
        sys.exit("no glyph named %r.%s" % (a.name, "  near: " + ", ".join(near) if near else ""))

    ch, cp = chr(byname[a.name]), byname[a.name]
    if a.char_only:
        print(ch)
        return

    if a.render:
        # a private-use glyph cannot be typed or pasted, so never ask a human to move it
        here = pathlib.Path(__file__).resolve().parent
        out = pathlib.Path(a.render)
        out.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(here / "make_mark.py"), "--font", str(font), "--text", ch,
               "--size", "512", "--ink", a.ink, "--name", a.name.replace("_", "-"),
               "--png", a.sizes, "--out-dir", str(out)]
        print("rendering %s  (U+%04X)" % (a.name, cp))
        print("  make_mark.py --font %s --name %s --png %s" % (font.name, cmd[8], a.sizes))
        import subprocess
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(r.stdout.strip()[-500:])
        if r.returncode != 0:
            sys.exit(r.stderr.strip()[-400:] or "make_mark.py failed")
        print("wrote marks into %s" % out)
        return
    print("name  : %s" % a.name)
    print("glyph : U+%04X   (write it as \\u%04x if you must embed it in source)" % (cp, cp))
    print("char  : %s" % ch)
    print("\nfeed it to the mark builder:")
    print('  python make_mark.py --font %s --text "%s" --size 512 --ink "#f4f7fa" \\' % (font.name, ch))
    print('      --name mark --png 16,32,48,64,192 --out-dir out/')
    print("\nnote: the private-use codepoint is version-specific. Look it up by name every time;")
    print("      do not paste the hex into a script, or the next font release breaks it.")


if __name__ == "__main__":
    main()
