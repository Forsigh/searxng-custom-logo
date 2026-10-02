# Surviving a SearXNG update

An update replaces the theme. Files you bind-mounted into the container survive, but the CSS and
templates that *reference* them do not. So the symptom after `docker compose pull` is usually not
"the logo reverted" - it is **"the logo is gone entirely"**, because the element that showed it
lives in a template or stylesheet that has just been replaced.

## What survives and what does not

| thing | after an image update |
|---|---|
| files in the bind-mounted custom dir | survive - they live outside the image |
| a new filename's `volumes:` line in `docker-compose.yaml` | survives - the compose file is yours |
| `?v=` stamps inside `base.html` | lost - the template is replaced |
| CSS rules inserted into the theme stylesheet | lost - the stylesheet is replaced |
| `settings.yml` | survives only if it is bind-mounted; otherwise it is inside the image |
| the running container's `Content-Length` cache | cleared by the recreate, then rebuilt from the new file |

## Detect the loss before a user does

1. After any update, diff the theme's template and stylesheet against the copies you kept.
2. Run `scripts/verify_deploy.py`. It fails loudly on an asset the server is not serving.
3. Load the page and confirm the logo **element** exists at all - a missing element and a
   zero-sized element look the same in a screenshot and have different causes.

## Order of operations after an update

1. Back up the custom dir and the patched theme files **before** updating.
2. Update.
3. Re-apply the CSS insertions. They must go immediately after the rule they override - never
   appended to the end of the minified file, where the parser silently drops them.
4. Re-stamp `?v=<new stamp>` on the stylesheet link in `base.html`.
5. Regenerate any `.br`/`.gz` siblings from the new file.
6. `docker restart searxng`.
7. Verify with `scripts/verify_deploy.py`.

## Keep the patch re-appliable, not remembered

Store the change as a script that inserts the rules and bumps the stamp, and run it after every
update. An edit kept as a script is re-appliable; an edit kept as a memory of what you did once has
to be rediscovered every time the theme changes. Two things make that script hard to write wrong:
stamp the stylesheet as well as the asset, and make the insertion idempotent so a second run does
not stack a second copy of the rules.

## Pin the version if updates are disruptive

`searxng/searxng:latest` moves under you. Pin a digest or tag while you are mid-work, then update
on purpose. A themed install is a fork of the default look, and every update is a small merge.
