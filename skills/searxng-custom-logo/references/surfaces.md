# searxng-custom-logo - surfaces

Part of the `searxng-custom-logo` skill. Load `SKILL.md` first for the routing table.

## Where each surface lives

| surface | how it renders | drawn at | container |
|---|---|---|---|
| front page | CSS background on `.index .title`, `contain` | ~609x115 | full width |
| results mark | `<img>` inside `#search_logo` | 153x48 | fixed ~202px column |
| page header | `<img class="logo">` | 212x40 | auto |
| favicon | `<link rel="icon">` in `base.html` and the custom `home.html` | 16-64px | browser chrome |

`#search_logo img{...height:48px}` in the theme CSS sets the mark's size. That
column is a fixed ~202px and does NOT grow with content: a wider mark overflows
both sides, collides with the search input, and can push its own left edge off
screen to a negative x. Size the asset by height, then measure.

## Making an effect readable on a small surface

An effect that reads large can be invisible small. Tear bands at 4-12% of cap
height are 1-2px on 14px caps: real motion, nothing to see. Fixes, in order:

1. **Bigger caps in the same slot.** One word filling the header height beats two
   sharing it -- 14.5px caps became 30px just by dropping the second word. Rebuild
   the asset tight; most of the old padding was doing nothing.
2. **Scale amplitudes as a fraction of cap height**, not in pixels, so the effect
   keeps its character when the render size changes.
3. Keep the second word if it is wanted, but build it tight too: the same slot then
   gives 19.8/13.9 instead of 14.5/10.1.

CSS filters can carry a single ink colour across themes (`brightness(0.1)` turns a
light mark dark). With two tones they invert wrong and the hierarchy breaks --
serve two files instead.

Keep `class="logo"` on the header img. Wrapping it in `<picture>` drops the class,
the sizing CSS stops matching, and it renders at natural size (e.g. 1800x340).

Animating a small surface is worth it ONLY if you make the caps big enough first.
At the old 144x48 lockup the caps were 14.5px and the motion was measurably
invisible; the same slot rebuilt tight gives 30px caps and full-contrast change on
nearly a third of frames. Keep the static SVG as the reduced-motion fallback either
way -- matching the animated asset's proportions so nothing shifts when it swaps in.
