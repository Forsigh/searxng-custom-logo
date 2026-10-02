# searxng-custom-logo - favicon

Part of the `searxng-custom-logo` skill. Load `SKILL.md` first for the routing table.

## The favicon is its own surface, and easy to get wrong

The tab icon is NOT the wordmark. It lives at `img/favicon.svg` + `favicon.png`
(+ `192.png` / `512.png` for apple-touch), referenced from `base.html` AND the
custom front page (`home.html`). Same deploy mechanics as any static file:
replace, regenerate `.br`/`.gz`, restamp, restart. The `?v=` bump must cover the
icon links in both templates -- and match the link by its href, not by attribute
order, because the apple-touch link orders `rel` before `href`.

"The icon is gone" almost always means the mark is invisible against the
browser's own chrome, not that the file is missing. A bare letter depends on the
chrome colour; a filled rounded tile does not:

- a tile of ANY tone can be rejected as a broken plate against real browser chrome
  (a slate #4a5260 tile was reported back as "broken for dark mode"). Prefer a **bare
  mark on a transparent background** and put the contrast in the ink, not a plate
- a bare mark needs a theme switch or it vanishes on one of the two chromes. Embed it
  in the SVG itself, with the LIGHT ink as the default so a browser that ignores the
  media query still works on dark chrome:
  `path { fill: #f4f7fa } @media (prefers-color-scheme: light) { path { fill: #14171c } }`
- do not trust that switch -- measure it. Draw the SVG into a canvas on the page and read
  the dominant opaque pixel colour while toggling `Emulation.setEmulatedMedia` with feature
  `prefers-color-scheme` dark/light. Chromium honours an embedded switch (measured ink
  #f4f7fa in dark, #14171c in light, 1184 opaque px, everything else transparent)
- with no tile the glyph can fill far more of the viewBox: ink width 68% -> 88%, which also
  buys back the small-size legibility a thin monoline face (Michroma) loses at 16px
- fit the letter by **ink width** (~68% of the side), never by cap height:
  Michroma's M is ~1.6x wider than its cap, so cap-fitting overflows the tile
- fontTools is y-up and SVG is y-down: flip with `scale(s,-s)` or every glyph
  renders upside down (an M comes out as a W)
- raster size must be computed **per output size**. A font size derived for the
  92px viewBox, reused in an 8x-supersampled canvas of another size, renders the
  same absolute glyph and silently yields 97% or 12% ink instead of 68%
- look at it at 16px on both a light and a dark background before shipping, and
  stamp the test page's URLs with `?v=` too -- an unversioned reference there
  serves the OLD cached file and looks like a bug in the new asset


## Branding without breaking accessibility

A rebrand is a visual change with invisible consequences. These get shipped by accident because
nothing in the default view shows them:

- **Keep the accessible name on the logo link.** The header mark is often the only link home. If it
  is an `<img>`, it needs real `alt` text; if the mark is a background image or an inline SVG, the
  link needs `aria-label`. `alt=""` on a logo link leaves screen-reader users with a nameless link.
- **Give a decorative mark `alt=""` deliberately.** The opposite mistake: a mark beside a text
  wordmark that already states the name will otherwise be announced twice.
- **Never encode state in colour alone.** A mark that turns red for an error, or a tinted icon that
  means "active", needs a text or shape cue as well.
- **Check the theme switch by emulation, not by eye.** A mark carrying an embedded
  `prefers-color-scheme` switch has to be measured on both branches. Emulate the media feature in
  devtools and read pixels back; the file containing the switch does not prove the switch fired.
- **An animation must be meaningful as a still.** An animated WebP inside an `<img>` cannot be paused
  by CSS, and `prefers-reduced-motion` cannot reach inside it. Design the effect to settle to a clean
  resting state and hold: someone who sees one frame, or who has motion disabled, must still see a
  correct and complete mark. An effect only legible mid-motion is broken.
- **Do not delete the page title or the visible wordmark to "clean up" the header.** The mark adds
  identity; the text carries meaning, and search engines, screen readers and new visitors all use it.

One check that catches most of it: browse the page with the keyboard only, then again with images
disabled. If the site becomes unusable, the branding is load-bearing and should not be.
