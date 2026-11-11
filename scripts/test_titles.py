#!/usr/bin/env python3
"""Fail if a built page title is over 60 characters or a description is over 160.

MONTH is an abbreviated month plus a year, as in "Sep 2026". Every month in
that format is checked, so a longer abbreviation cannot slip past a build that
happened to use a short one. Meta, Open Graph, and Twitter descriptions are
the same string.
"""
import datetime
import html
import os
import re
import sys

LIMIT = 60
DESC_LIMIT = 160
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def month_names():
    return [datetime.date(2026, month, 1).strftime("%b %Y") for month in range(1, 13)]


def rendered_titles(dist):
    found = []
    for dirpath, _, files in os.walk(dist):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(dirpath, name)
            raw = open(path, encoding="utf-8").read()
            match = re.search(r"<title>(.*?)</title>", raw)
            if not match:
                continue
            rel = os.path.relpath(path, dist)
            found.append((rel, html.unescape(match.group(1))))
    return found


def title_errors(dist):
    if not os.path.isdir(dist):
        return [f"{dist} is missing; build the site before checking titles"]
    titles = rendered_titles(dist)
    if not titles:
        return ["no rendered titles found"]
    names = month_names()
    longest = max(names, key=len)
    errors = []
    for rel, title in titles:
        widened = title
        for name in names:
            if name in widened and name != longest:
                widened = widened.replace(name, longest)
        if len(title) > LIMIT or len(widened) > LIMIT:
            errors.append(
                f"{rel} title is {len(title)} characters"
                f" ({len(widened)} with {longest}): {title}"
            )
    return errors


def rendered_descriptions(dist):
    found = []
    for dirpath, _, files in os.walk(dist):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(dirpath, name)
            raw = open(path, encoding="utf-8").read()
            meta = re.search(r'<meta name="description" content="(.*?)"', raw)
            if not meta:
                continue
            og = re.search(r'<meta property="og:description" content="(.*?)"', raw)
            tw = re.search(r'<meta name="twitter:description" content="(.*?)"', raw)
            rel = os.path.relpath(path, dist)
            found.append((
                rel,
                html.unescape(meta.group(1)),
                html.unescape(og.group(1)) if og else None,
                html.unescape(tw.group(1)) if tw else None,
            ))
    return found


def description_errors(dist):
    if not os.path.isdir(dist):
        return [f"{dist} is missing; build the site before checking descriptions"]
    descriptions = rendered_descriptions(dist)
    if not descriptions:
        return ["no rendered descriptions found"]
    errors = []
    for rel, meta, og, twitter in descriptions:
        if len(meta) > DESC_LIMIT:
            errors.append(f"{rel} description is {len(meta)} characters: {meta}")
        if og != meta or twitter != meta:
            errors.append(f"{rel} og or twitter description does not match the meta description")
    return errors


def main():
    dist = os.path.join(ROOT, "dist")
    errors = title_errors(dist) + description_errors(dist)
    if errors:
        raise SystemExit("title and description check failed:\n- " + "\n- ".join(errors))
    titles = rendered_titles(dist)
    descriptions = rendered_descriptions(dist)
    print(f"ok {len(titles)} titles are {LIMIT} characters or fewer")
    print(f"ok {len(descriptions)} descriptions are {DESC_LIMIT} characters or fewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
