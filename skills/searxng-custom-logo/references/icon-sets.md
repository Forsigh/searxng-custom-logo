# Icon marks from a free icon font

Most of this skill assumes the mark is a letter rendered from a text face. If you would
rather use a real icon - a magnifier, a compass, a rocket - you do not need an SVG
rasteriser. PIL cannot read SVG, but it reads any TTF or OTF, and icon sets ship as fonts.

## The trap: never hardcode the codepoint

Icon fonts park their glyphs at private-use codepoints (U+E000-U+F8FF). Those move between
releases, and a glyph can be reassigned. A script that pastes in `\uf002` works until the font
updates, then silently renders the wrong picture - no error, just a different icon.

Every one of these sets keeps a real glyph name in the font's `cmap`, so look the icon up by
name. `scripts/icon_glyph.py` does exactly that:

```bash
python icon_glyph.py --font fa-solid-900.ttf --name magnifying-glass
python icon_glyph.py --font fa-solid-900.ttf --name star --char-only
python icon_glyph.py --font bootstrap-icons.ttf --name compass --find   # list near matches
python icon_glyph.py --font fa-solid-900.ttf --name magnifying-glass --render out/
```

`--render` calls `make_mark.py` for you. Use it: a private-use character cannot be typed or
pasted, so asking a human to carry it between commands is a dead end.

## Free sets that actually work

| set | file | licence |
|---|---|---|
| Font Awesome Free | `fa-solid-900.ttf` | icons CC BY 4.0, font SIL OFL |
| Material Symbols | `MaterialSymbolsOutlined[FILL,GRAD,opsz,wght].ttf` | Apache 2.0 |
| Bootstrap Icons | `bootstrap-icons.woff2` | MIT |
| Ionicons | `ionicons.ttf` | MIT |
| Phosphor | `Phosphor.ttf` | MIT |

**woff2 needs converting first.** PIL cannot open it. Bootstrap Icons ships woff2 only:

```bash
python icon_glyph.py --font bootstrap-icons.woff2 --name search --to-mark-font bootstrap-icons.ttf
```

That needs `brotli` installed, and fontTools prints a harmless
`extra bytes in post.stringData array` while converting. The result opens fine.

**Licence trap.** For Font Awesome Free the *font file* is SIL OFL but the *pictures* are
CC BY 4.0, which requires attribution wherever you redistribute them. A repo whose preview
images show those icons has to carry the credit. Check the set's own LICENSE - do not assume
one licence covers both halves.

## What survives at 16px

Rendering the same six icons from three sets at 16px and 64px shows a consistent pattern:
stroke weight decides small-size legibility, not detail. Font Awesome Solid and Bootstrap
Icons hold up; Material Symbols Outlined is thinner and greys out sooner. If your mark is an
outline icon at favicon size, prefer the set's filled or heavier variant, or draw the icon at
the size the browser actually draws and judge it there - `references/favicon.md`.

An icon mark also has a job a letter mark does not: at 16px the picture has to survive with
its interior detail gone. A magnifier keeps its diagonal; a detailed pictogram becomes a
blob. Test the actual icon, not a representative one.
