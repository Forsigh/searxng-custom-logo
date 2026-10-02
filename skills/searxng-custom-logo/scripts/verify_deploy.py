#!/usr/bin/env python3
"""Prove the deployed logo is the one actually being served, and that the classic deploy traps
are not silently in play.

All of them look identical in a browser - "the logo is broken" - so check them mechanically
rather than trusting a hard refresh.

  python verify_deploy.py --base-url http://localhost:8080 --compose ./docker-compose.yaml
  python verify_deploy.py --base-url https://search.example.com --dir ./custom --only 'logo*,favicon*'

The set that must be served comes from the **compose mounts**, not from the directory. A custom
dir legitimately holds sources and experiments that were never mounted; checking those reports
failures that are not failures. Files in the dir with no mount line are listed separately, as
hygiene, not as an error.

Per mounted asset it checks:
  1. the mount's host file exists           (a mount line pointing at nothing is silent)
  2. the URL answers 200                    (a new filename with no mount line, or no recreate)
  3. the served bytes equal the file         (a stale sibling or a stale cache serves old bytes)
  4. Content-Length equals the body length   (a stale Content-Length aborts mid-response)
  5. .br / .gz siblings decompress to the same bytes as the plain file

It also checks that the theme stylesheet link and any reference to a deployed asset carry a
?v= stamp, because an unstamped reference keeps browsers on the previous bytes.

Exit code is 0 only when every check passes, so it can gate a deploy step.
"""
import argparse
import gzip
import hashlib
import pathlib
import re
import sys
import urllib.error
import urllib.request

ASSET_SUFFIXES = {".svg", ".png", ".webp", ".gif", ".jpg", ".jpeg", ".ico", ".css"}


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def fetch(url, timeout=20):
    """Return (status, headers, body). A truncated body is the interesting failure, so report it
    instead of raising."""
    req = urllib.request.Request(url, headers={"User-Agent": "searxng-logo-verify",
                                               "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), b""
    except Exception as e:  # noqa: BLE001 - any transport failure is a result here
        return None, {}, str(e).encode()


def url_for_container_path(container_path, static_path):
    """SearXNG serves <container>/searx/static/... as /static/... . Fall back to the given prefix."""
    marker = "/searx/static/"
    if marker in container_path:
        return "/static/" + container_path.split(marker, 1)[1]
    return "%s/%s" % (static_path.rstrip("/"), pathlib.PurePosixPath(container_path).name)


def mounted_pairs(compose_path):
    """Return ([(host_path, container_path)], long_form_count) from a compose file's mounts.

    Handles the short form (`- ./a:/b`). The long `type: bind` mapping form is not parsed; report
    that rather than silently checking nothing.
    """
    text = compose_path.read_text(encoding="utf-8", errors="replace")
    pairs, long_form = [], 0
    try:
        import yaml  # noqa: PLC0415 - optional, only better than the fallback
        doc = yaml.safe_load(text) or {}
        for svc in (doc.get("services") or {}).values():
            for vol in (svc.get("volumes") or []):
                if isinstance(vol, str) and ":" in vol:
                    host, cont = vol.split(":", 1)
                    pairs.append((host.strip(), cont.strip()))
                elif isinstance(vol, dict):
                    long_form += 1
    except ImportError:
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("-") and ":" in line:
                host, cont = line[1:].split(":", 1)
                host, cont = host.strip().strip("'\""), cont.strip().strip("'\"")
                if host.startswith(("./", "../", "/")) or re.match(r"^[A-Za-z]:[\\/]", host):
                    pairs.append((host, cont))
    return pairs, long_form


def check_asset(base, url_path, path):
    url = "%s%s" % (base.rstrip("/"), url_path)
    problems = []
    status, headers, body = fetch(url)
    if status is None:
        return url, ["request failed: %s" % body.decode("utf-8", "replace")[:120]]
    if status != 200:
        return url, ["HTTP %s - not served. A new filename needs a mount line AND "
                     "docker compose up -d, not just a restart (references/deploy-and-cache.md)"
                     % status]

    disk = path.read_bytes()
    cl = headers.get("Content-Length")
    if cl is not None and cl.isdigit() and int(cl) != len(body):
        problems.append("Content-Length says %s but the body is %d bytes - stale length, "
                        "docker restart searxng" % (cl, len(body)))
    if sha(body) != sha(disk):
        problems.append("served bytes differ from the file on disk (%s vs %s) - a stale .br/.gz "
                        "sibling, or an upstream cache" % (sha(body), sha(disk)))
    for suffix in (".br", ".gz"):
        sib = path.with_name(path.name + suffix)
        if not sib.exists():
            continue
        try:
            raw = sib.read_bytes()
            plain = gzip.decompress(raw) if suffix == ".gz" else __import__("brotli").decompress(raw)
            if sha(plain) != sha(disk):
                problems.append("%s sibling decompresses to different bytes than the plain file"
                                % suffix)
        except ImportError:
            problems.append("%s exists but brotli is not installed, so it cannot be compared"
                            % suffix)
        except Exception as e:  # noqa: BLE001
            problems.append("%s sibling unreadable: %s" % (suffix, e))
    return url, problems


def check_stamps(base, names):
    """A reference with no ?v= keeps browsers on the previous bytes after a change.

    Scoped to the stylesheet link and to the deployed assets. Flagging every unstamped /static/
    reference on the page buries the two that matter under the theme's own.
    """
    status, _h, body = fetch(base.rstrip("/") + "/")
    if status != 200:
        return ["could not load the front page (HTTP %s)" % status]
    html = body.decode("utf-8", "replace")
    problems = []
    for href in re.findall(r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']', html):
        if "?v=" not in href:
            problems.append("theme stylesheet linked with no ?v= stamp: %s" % href)
    for n in names:
        for ref in re.findall(r'["\']([^"\']*%s[^"\']*)["\']' % re.escape(n), html):
            if "?v=" not in ref:
                problems.append("%s referenced with no ?v= stamp: %s" % (n, ref))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True, help="e.g. http://localhost:8080")
    ap.add_argument("--compose", type=pathlib.Path,
                    help="docker-compose.yaml - the mounts define what must be served")
    ap.add_argument("--dir", type=pathlib.Path, help="custom dir, for the unmounted-file note")
    ap.add_argument("--static-path", default="/static/themes/simple/img",
                    help="URL prefix, only used when a mount path cannot be mapped")
    ap.add_argument("--only", help="comma-separated globs, e.g. 'logo*,favicon*'")
    a = ap.parse_args()
    if not a.compose and not a.dir:
        ap.error("give --compose (preferred) or --dir")

    targets = []          # (url_path, host file)
    seen_hosts = set()
    long_form = 0
    if a.compose:
        if not a.compose.exists():
            sys.exit("no such compose file: %s" % a.compose)
        pairs, long_form = mounted_pairs(a.compose)
        root = a.compose.parent
        for host, cont in pairs:
            p = pathlib.Path(host)
            if not p.is_absolute():
                p = (root / host).resolve()
            seen_hosts.add(p.name)
            if p.suffix.lower() not in ASSET_SUFFIXES:
                continue
            targets.append((url_for_container_path(cont, a.static_path), p))
    else:
        for p in sorted(a.dir.iterdir()):
            if p.is_file() and p.suffix.lower() in ASSET_SUFFIXES and not p.name.endswith((".br", ".gz")):
                targets.append(("%s/%s" % (a.static_path.rstrip("/"), p.name), p))

    if a.only:
        globs = [g.strip() for g in a.only.split(",") if g.strip()]
        targets = [(u, p) for u, p in targets
                   if any(pathlib.PurePath(p.name).match(g) for g in globs)]
    if not targets:
        sys.exit("nothing to check" + (" - no asset mounts found in %s" % a.compose.name if a.compose else ""))

    print("checking %d mounted asset(s) against %s" % (len(targets), a.base_url))
    failures = 0
    for url_path, path in targets:
        if not path.exists():
            failures += 1
            print("\n  FAIL  %s" % url_path)
            print("        the mount points at %s, which does not exist" % path)
            continue
        url, problems = check_asset(a.base_url, url_path, path)
        if problems:
            failures += 1
            print("\n  FAIL  %s" % url)
            for pr in problems:
                print("        %s" % pr)
        else:
            print("  ok    %-44s %s" % (path.name, sha(path.read_bytes())))

    print("\nchecking reference stamps on the front page")
    stamp_problems = check_stamps(a.base_url, sorted({p.name for _u, p in targets}))
    failures += len(stamp_problems)
    for pr in stamp_problems:
        print("  FAIL  %s" % pr)
    if not stamp_problems:
        print("  ok    the stylesheet and every deployed asset carry a ?v= stamp")

    # hygiene, not a failure: files in your custom dir that nothing mounts
    if a.dir and a.dir.is_dir():
        unmounted = sorted(p.name for p in a.dir.iterdir()
                           if p.is_file() and p.suffix.lower() in ASSET_SUFFIXES
                           and not p.name.endswith((".br", ".gz"))
                           and (not a.compose or p.name not in seen_hosts))
        if unmounted and a.compose:
            print("\nnote: %d file(s) in %s are not mounted, so they are never served:"
                  % (len(unmounted), a.dir))
            print("      %s%s" % (", ".join(unmounted[:12]), " ..." if len(unmounted) > 12 else ""))
    if long_form:
        print("\nnote: %d volume(s) use the long type:/source:/target: form and were not parsed;"
              % long_form)
        print("      pass --only or --dir to check those explicitly")

    print("\n%s" % ("all checks passed" if not failures else "%d check(s) failed" % failures))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
