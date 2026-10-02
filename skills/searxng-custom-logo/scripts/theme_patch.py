#!/usr/bin/env python3
"""Re-apply a theme patch after a SearXNG update, idempotently.

An update replaces the theme, taking your CSS insertions and your ?v= stamp with it. Hand-editing
them back every time is how a working install quietly turns into a broken one. Both operations
here are safe to run repeatedly: they detect what is already applied, skip it, and the caller can
verify the result by reading the file back.

  # insert rules immediately after a rule you are overriding (never at the end of the file)
  theme_patch.py --css ./custom/sxng-ltr.min.css \\
      --after '.index .title' --rules ./custom/logo.css --marker '/* custom-logo */'

  # bump the cache-busting stamp on the stylesheet link
  theme_patch.py --html ./custom/base.html --stamp 20261002a

  # see what would change, touch nothing
  theme_patch.py --css ... --after ... --rules ... --dry-run

Why after a rule and not at the end: the minified theme stylesheet ends with unbalanced braces, and
rules appended past the end are dropped by the parser with no error. A rule present in the file can
still be unused - check the browser's own stylesheet list, not the source text. A .bak sits beside
every file this rewrites.
"""
import argparse
import pathlib
import re
import shutil
import sys


def find_rule_span(text, selector):
    """Return (open_brace, close_brace) for the selector's rule, by brace matching.

    A plain string search is not enough: the theme is minified, and several selectors can appear
    before a brace. Take the last occurrence of a selector followed by '{' and match from there.
    """
    pat = re.compile(re.escape(selector) + r"\s*\{", re.I)
    matches = list(pat.finditer(text))
    if not matches:
        return None
    start = text.index("{", matches[-1].start())
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return start, i
    return start, None      # unbalanced: the file ends mid-rule


def patch_css(path, selector, rules, marker, dry_run):
    text = path.read_text(encoding="utf-8", errors="replace")
    if marker and marker in text:
        return "already applied (marker found), nothing to do"
    span = find_rule_span(text, selector)
    if span is None:
        return ("FAILED: selector %r not found - the theme changed, so re-check where to insert"
                % selector)
    _open, close = span
    if close is None:
        return ("FAILED: the rule for %r never closes, so inserting would land in the unbalanced "
                "tail the parser drops" % selector)
    depth = 0
    for ch in text[:close]:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
    if depth != 1:
        return ("FAILED: the rule for %r sits inside an unclosed block (brace depth %d at that "
                "point), so anything inserted there is dropped along with it" % (selector, depth))
    block = "\n" + rules.strip() + "\n"
    if not dry_run:
        shutil.copy2(path, str(path) + ".bak")
        path.write_text(text[:close + 1] + block + text[close + 1:], encoding="utf-8")
    return "inserted %d chars after %r" % (len(block), selector)


def patch_stamp(path, stamp, dry_run):
    """Rewrite ?v=<anything> on the stylesheet link, whatever the previous stamp was."""
    text = path.read_text(encoding="utf-8", errors="replace")
    pat = re.compile(r'(<link[^>]+href=["\'][^"\']*?\.css)\?v=[^"\']*(["\'])', re.I)
    if not pat.search(text):
        return "FAILED: no stylesheet link with a ?v= stamp found - check how base.html links it"
    if "?v=%s" % stamp in pat.search(text).group(0):
        return "already at stamp %s, nothing to do" % stamp
    if not dry_run:
        shutil.copy2(path, str(path) + ".bak")
        path.write_text(pat.sub(lambda m: "%s?v=%s%s" % (m.group(1), stamp, m.group(2)), text),
                        encoding="utf-8")
    return "stamped the stylesheet link with %s" % stamp


def main():
    ap = argparse.ArgumentParser(
        description="Re-apply theme CSS insertions and the ?v= stamp after a SearXNG update.",
        epilog="Run it after every update instead of editing by hand; both operations are "
               "idempotent. Finish with: docker restart searxng, then verify_deploy.py.\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--css", type=pathlib.Path, help="theme stylesheet to insert into")
    ap.add_argument("--after", help="selector of the rule to insert after, e.g. '.index .title'")
    ap.add_argument("--rules", type=pathlib.Path, help="file holding the rules to insert")
    ap.add_argument("--marker", default="/* custom-logo */",
                    help="comment marking the insert, so a re-run can detect it")
    ap.add_argument("--html", type=pathlib.Path, help="base.html to re-stamp")
    ap.add_argument("--stamp", help="new ?v= value, e.g. the date")
    ap.add_argument("--dry-run", action="store_true", help="report only, change nothing")
    a = ap.parse_args()
    if not a.css and not a.html:
        ap.error("give --css (insert rules) and/or --html --stamp")

    failures = 0
    if a.css:
        if not a.after or not a.rules:
            ap.error("--css needs --after and --rules")
        if not a.rules.exists():
            sys.exit("no such rules file: %s" % a.rules)
        rules = a.rules.read_text(encoding="utf-8")
        if a.marker and a.marker not in rules:
            rules = "%s\n%s" % (a.marker, rules)     # make the insert detectable next time
        msg = patch_css(a.css, a.after, rules, a.marker, a.dry_run)
        print("css   : %s" % msg)
        failures += msg.startswith("FAILED")
    if a.html:
        if not a.stamp:
            ap.error("--html needs --stamp")
        msg = patch_stamp(a.html, a.stamp, a.dry_run)
        print("html  : %s" % msg)
        failures += msg.startswith("FAILED")

    print("\n%s" % ("dry run, nothing written" if a.dry_run else
                     ("all done" if not failures else "%d step(s) failed" % failures)))
    print("then: docker restart searxng, and verify with scripts/verify_deploy.py")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
