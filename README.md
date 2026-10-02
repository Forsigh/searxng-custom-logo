# agent-skills

Agent Skills I use and maintain. Plain [Agent Skills](https://github.com/anthropics/skills)
format — `SKILL.md` with frontmatter, plus `references/` for depth and `scripts/` for anything
runnable — so they drop into Hermes, Claude Code, or any compatible harness.

Everything here is written to be read by an agent mid-task: the traps first, the theory second,
and a verification step for every claim that could otherwise be taken on faith.

## Install

Hermes:

```bash
hermes skills tap add Forsigh/agent-skills
hermes skills install searxng-custom-logo --yes
```

Other harnesses: copy the directory under `skills/` into wherever your skills live.

## Skills

### searxng-custom-logo

Branding a containerised SearXNG — wordmark, animated front page, results mark, and the favicon.

Deploying a logo to a containerised SearXNG has five traps that each present as "the logo is
broken" for a different reason: a new filename that is invisible until it is mounted, a stale
`Content-Length` that aborts every request until the container restarts, a missing `?v=` bump
that leaves browsers on old CSS, CSS rules silently dropped by the asset's own trailing braces,
and precompressed siblings still serving the previous image. The skill walks all five, then
covers the parts that actually take the time: measuring which size the page really draws,
making an effect legible at that size, building an animated WebP that plays, and a favicon that
survives both browser themes.

Includes two scripts:

- `make_mark.py` — render a glyph or short word from any font as a transparent SVG mark plus PNG
  fallbacks, optionally with an embedded `prefers-color-scheme` ink switch.
- `font_contact_sheet.py` — contact sheet of candidate typefaces at real render sizes, so a
  face is chosen by how it looks at 16px rather than at poster size.

No fonts are bundled: pass your own, under its licence. `references/fonts-and-licensing.md`
covers what the OFL and Apache licences do and do not permit, and why a rendered glyph outline
is the safe way to ship a wordmark.

## Layout

```
skills/<name>/SKILL.md      the always-loaded hub: rules, quick start, routing table
skills/<name>/references/   depth, loaded only when the hub routes you there
skills/<name>/scripts/      runnable helpers
```

## Licence

MIT — see `LICENSE`. Individual skills may carry their own notes where a dependency or a
typeface licence differs.
