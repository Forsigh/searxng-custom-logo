---
name: searxng-custom-logo
description: "Use when changing the logo on a self-hosted SearXNG."
version: 2.1.0
author: Forsigh
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [searxng, branding, logo, favicon, animated-webp, docker, css]
    category: productivity
    related_skills: [searxng-provider-patches, docker-container-maintenance]
---

# Custom SearXNG Logo / Wordmark

Branding a containerised SearXNG: wordmark, front-page animation, results mark, and
favicon. Deploying any of them has five traps that each look like the logo is
"broken" for a different reason. Check every one.

Written against a stock `searxng/searxng` Docker install. Every measurement here is
an example to re-measure on yours, not a constant -- the theme's own dimensions vary
with version and with how much of the page you have customised.

## Prerequisites

- a containerised SearXNG on the `simple` theme, with `docker` on PATH
- Python with `Pillow`, `fontTools` and `numpy`; `brotli` if you serve `.br` siblings
- `ffmpeg` built with `libwebp_anim` -- only if you are building an animated WebP
- the typefaces you intend to use, under their own licences (`references/fonts-and-licensing.md`)
- for an icon mark instead of a letter: a free icon font, plus `brotli` if it ships woff2 only
  (`references/icon-sets.md`)

## Quick start

1. Render the asset at **the size the page actually draws it**, not the size the source
   file happens to be -- `references/surfaces.md` shows how to measure that.
2. Copy it into the bind-mounted custom dir. Keep an **existing filename** if there is
   one; a new filename also needs a mount line and `docker compose up -d`.
3. Regenerate any `.br`/`.gz` siblings.
4. Bump `?v=<stamp>` on the reference **and** on the stylesheet link.
5. `docker restart searxng`, then verify the served bytes equal the file on disk.

Steps 3-5 are the ones that get skipped, and skipping any of them produces the same
symptom: "the logo vanished".

## Where to look next

| question | file |
|---|---|
| which surface renders where, and how big is it really | `references/surfaces.md` |
| the mark is fine large but unreadable in its slot | `references/surfaces.md` |
| favicon: bare mark or tile, theme switching, fitting a glyph | `references/favicon.md` |
| building an animated WebP that actually plays | `references/animated-webp.md` |
| the file changed but the browser still serves the old one | `references/deploy-and-cache.md` |
| proving any of it worked | `references/verification.md` |
| which faces survive at 16px, and their licences | `references/fonts-and-licensing.md` |
| rendering an SVG + PNG mark from a font | `scripts/make_mark.py` |
| shortlisting candidate faces at real tab sizes | `scripts/font_contact_sheet.py` |
| using a real icon instead of a letter | `references/icon-sets.md`, `scripts/icon_glyph.py` |

## Symptom to cause

| symptom | most likely cause |
|---|---|
| logo gone entirely, no error anywhere | `?v=` not bumped on the stylesheet, or the file is not mounted at all |
| logo appears once then requests abort | stale `Content-Length` -- restart the container |
| a new CSS rule has no effect although the file contains it | rule appended to the end of the minified theme CSS |
| an old image is served after replacing the file | stale `.br`/`.gz` sibling, or no restamp |
| icon invisible on one browser theme | fixed ink colour instead of a theme switch (`references/favicon.md`) |
| icon shows a coloured plate behind it | a page colour baked into the asset instead of straight alpha |
| header logo renders at an absurd size | `class="logo"` lost, e.g. by wrapping the img in `<picture>` |
| animation plays in the builder but not in the page | source frames identical or blank -- verify before blaming the encoder |
| the icon mark changed picture after a font update | a hardcoded private-use codepoint -- resolve the glyph by name (`references/icon-sets.md`) |

## When to Use

- Replacing or adding a logo/wordmark on a self-hosted SearXNG
- Making one animated, or debugging an animation that will not play
- A logo that vanished, shows a coloured box, or comes out the wrong size
- Changing the favicon / tab icon

## The container mounts each file individually

`docker-compose.yaml` mounts single files, not the directory. A **new filename is
invisible to the server** until you add a mount line AND recreate the container:

```yaml
      - ./custom/mylogo.webp:/usr/local/searxng/searx/static/themes/simple/img/mylogo.webp
```

Replacing an existing filename needs no mount change, but still needs the restart below.

## Always restart the container after replacing a static file

SearXNG caches the static file's length. Without a restart it sends a stale
`Content-Length` and **every request aborts**. `docker restart searxng` clears it.

## Cache-bust the asset AND the stylesheet

Bump `?v=<stamp>` on every changed reference **and on the CSS link in `base.html`**.
Missing the stylesheet stamp leaves browsers on old CSS pointing at deleted files --
the logo simply vanishes with no error. Regenerate `.br`/`.gz` siblings too, or a
stale compressed sibling serves the old content.

## Never append CSS rules to the end of the minified theme CSS

The SearXNG theme CSS ends with unbalanced braces; rules appended at the end are
**silently dropped by the parser**. Insert them immediately after the rule they
override. Verify with `document.styleSheets` in a browser -- not by reading the file,
which will show the rule present while the browser never applies it.

## Sharing this skill

It is written to be installable by anyone: no machine-specific paths in this hub or in
`references/`, except one reference file that records what is deployed on a particular
instance. The staging step drops that file together with any table row pointing at it, so
the published copy carries no dangling links. The two scripts take their fonts as
arguments and ship no font files, because the font licences are the user's to accept. All three
resolve a glyph or a glyph name; none bundles artwork.

The format is plain Agent Skills (frontmatter + markdown + `references/` + `scripts/`),
so the directory drops into any compatible harness as-is. Only the deployment targets
in `references/surfaces.md` are SearXNG-specific; the mark-building and verification
material in `references/favicon.md` and `references/verification.md` applies to any
web surface that renders an SVG or an animated WebP.
