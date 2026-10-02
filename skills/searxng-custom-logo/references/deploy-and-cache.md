# searxng-custom-logo - deploy and cache

Part of the `searxng-custom-logo` skill. Load `SKILL.md` first for the routing table.

## Changing an asset's content without changing its filename

The URL is the cache key. If the filename stays the same, a browser keeps the old
bytes. Restamp the asset URLs **inside the CSS** as well as the stylesheet link in
`base.html`, or the old animation keeps being served from cache.
