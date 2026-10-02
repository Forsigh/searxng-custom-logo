# Walkthrough: font file to deployed mark

A complete run against a stock Docker install at `http://localhost:8080`. Substitute your own
face, letter and paths. Every command is copy-pasteable, and each step says what it proves.

## 1. Choose the face by the small chip, not the big mark

```bash
python scripts/font_contact_sheet.py --text "M" \
  --fonts Lexend.ttf Inter.ttf Montserrat-ExtraBold.ttf \
  --out-dir out/sheet
```

Open the sheet and look at the 16px column. A face that wins at 64px can lose at 16px, and the
small size is the one your users see in a tab.

## 2. Render the mark

```bash
python scripts/make_mark.py --font Lexend.ttf --weight 700 --text "M" \
  --size 92 --ink "#f4f7fa" --name mark \
  --png 16,32,48,192 --out-dir out/
```

You get a transparent `mark.svg` plus PNG fallbacks. `--ink` is the mark's colour; pass
`--ink-light`/`--ink-dark` for a mark that switches with the browser theme.

For an icon instead of a letter, resolve it by name first - never paste a codepoint:

```bash
python scripts/icon_glyph.py --font fa-solid-900.ttf --name magnifying-glass --render out/
```

## 3. Measure the slot before trusting any size

The page draws the mark at whatever size the stylesheet says, which is often not the size you
rendered. Check the live element:

```js
// in the browser console on the search page
const el = document.querySelector('.index .title img, .logo img, img.logo');
console.log(el.getBoundingClientRect(), el.naturalWidth);
```

Re-render at the size actually drawn. `references/surfaces.md` lists where each surface comes from.

## 4. Put the file where the container can see it

Look at `volumes:` in `docker-compose.yaml`. The custom dir is usually mounted **one file per
line**, not as a directory:

```yaml
    volumes:
      - ./custom/mark.svg:/usr/local/searxng/searx/static/themes/simple/img/mark.svg
```

- Replacing an existing filename: no compose change.
- Adding a new filename: a new mount line AND `docker compose up -d` (a restart is not enough).

## 5. Restart, then verify

```bash
docker restart searxng
# the mounts in your compose file decide what must be served, so point it at both
python scripts/verify_deploy.py --base-url http://localhost:8080 \
  --compose ./docker-compose.yaml --dir ./custom
```

Do not stop at "it looks right". The restart clears the cached `Content-Length`; skipping it makes
every request for that file abort even though the file on disk is perfect.

## Not using Docker?

The file locations differ and the traps do not. A package install keeps the theme under the
package directory, e.g. `<venv>/lib/python3.X/site-packages/searx/static/themes/simple/`, and a
system install commonly uses `/usr/local/searxng/searx/static/themes/simple/`. Two differences
that matter:

- there is no mount step, so a new filename is visible immediately - step 4 is unnecessary;
- **a package upgrade overwrites the theme**, and unlike a bind mount you have no copy. Keep your
  patched template and stylesheet outside the package tree and re-apply them
  (`references/upgrades-and-updates.md`).

If the server runs behind a reverse proxy, add the cache-bust to the proxy's rules too, or it will
keep serving the previous image from its own cache.

## When it still does not appear

The symptom-to-cause table in `SKILL.md` covers every variant. The three most common after a
correct-looking deploy:

| what you see | what it is |
|---|---|
| nothing at all, no error | `?v=` not bumped on the stylesheet, so browsers hold old CSS pointing at a path that no longer exists |
| appears once, then requests abort | stale `Content-Length` - restart the container |
| an old image after replacing the file | a stale `.br`/`.gz` sibling, or the proxy's cache |
