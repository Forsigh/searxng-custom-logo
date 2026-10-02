# Fonts: which ones work, and how to use them legally

This skill ships **no font files**. The scripts take a font path as an argument. That is
deliberate: the licences are the installer's to accept, and redistributing a font file
inside a skill is the one thing here that can genuinely get someone in trouble.

## Check the licence before you ship an outline

The common display/UI faces used for marks are SIL Open Font License (OFL) or Apache-2.0,
which permit embedding and redistribution of **rendered output** (an SVG outline of one
glyph, or a PNG). Both licences have conditions worth knowing:

- OFL: keep the copyright notice with the font, do not sell the font itself, and if you
  distribute a *modified* font file it must stay under the OFL with a changed name.
  Rendering an outline into your own logo is fine and is what the licence is for.
- Apache-2.0: keep the NOTICE file; same practical result for rendered marks.
- Some commercial display faces permit desktop use but not embedding. If the font is not
  OFL/Apache, read its EULA before you convert a glyph to a path, because a vector outline
  of a letterform is arguably a derivative work.
- Converting a glyph to paths removes the font from the deliverable, which is exactly what
  you want: the deployed SVG needs no font on the server and no licence file in the repo.

Verify rather than trust a memory: `fc-query --format '%{family} %{style}\n' font.ttf` or
read the `name` table. The scripts here keep no attribution table of their own.

## Pin variable fonts, or your three outputs disagree

A variable font renders at a default instance unless you say otherwise, so the SVG outline,
the PNG and your preview can silently be three different weights. Instance it first:

```python
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
tt = TTFont("Lexend.ttf")
instantiateVariableFont(tt, {"wght": 700}, inplace=True)
tt.save("Lexend-700.ttf")   # then feed this to both the outline and the raster path
```

`make_mark.py` does this for you when you pass `--weight`.

## Fit the ink box, not the cap height

Fitting by cap height overflows the canvas for a wide face. Fit by the ink box instead, and
fit **both axes** so whichever binds first wins. Measured ratios (ink width / ink height) for
the same capital M:

| face | M ink ratio | binds on |
|---|---|---|
| Michroma | 1.57 | width |
| Lexend 700 | 1.00 | either (both land at the fit fraction) |

A width-only fit therefore happens to work for a wide display face and quietly pushes a
near-square face (most text faces at bold weights) past the canvas vertically.

## What actually survives at 16px

Judged on a rendered contact sheet at real tab sizes, not on how the letter looks at 200px:

| works well | why |
|---|---|
| Inter 800, Manrope 800, Lexend 700 | open counters, generous stroke weight, hold shape when rasterised small |
| Montserrat 800, JetBrains Mono 700 | heavy and simple; the skeleton survives downscaling |

| avoid for a 16px mark | why |
|---|---|
| hairline monoline display faces (e.g. Michroma at 400) | the single stroke collapses to ~1px and greys out |
| very wide or rounded-techno faces (e.g. Audiowide, Zen Dots) | wide rounded details blur and fill in at tab size |
| anything decorative with interior detail | detail is the first thing lost |

Use `scripts/font_contact_sheet.py` to run this test on your own shortlist before committing,
and judge the 16px column. A face that reads beautifully at 64px tells you nothing.
