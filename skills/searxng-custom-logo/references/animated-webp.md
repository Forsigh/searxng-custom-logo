# searxng-custom-logo - animated webp

Part of the `searxng-custom-logo` skill. Load `SKILL.md` first for the routing table.

## Animated WebP that actually plays

**Transparency works** -- use it. A transparent animated WebP composites over any
page colour, so no page-colour matching is needed and no plate can ever show.
Earlier failures that looked like "Chromium will not animate alpha" were in fact
blank or identical source frames; check the frames before blaming the encoder.

Use straight (un-premultiplied) alpha: colour = the ink colour everywhere, alpha =
coverage. Ink differs per theme (light ink for dark pages, dark ink for light
pages), so serve one file per theme via `@media (prefers-color-scheme: light)`.

Only bake a page colour if you genuinely cannot ship alpha -- then measure the real
colour live and remember a wrong guess is visible as a plate.

- do NOT `Image.alpha_composite()` before a P-mode conversion: the result silently
  writes as a **single frame** (0 ANMF). Composite in numpy, or render the ink
  straight onto RGBA.
- recipe: render frames, keep every 2nd of 300 (30fps), resize to the size the page
  actually draws (~900x170 for the front page), save RGBA with
  `method=6, quality=80, lossless=False`, durations summing exactly 5000ms.
- alpha costs size: ~730KB transparent vs ~390KB opaque for the same mark.
- `@media (prefers-reduced-motion: reduce)` must come AFTER the colour-scheme
  override, or a light page with reduced motion still animates.
