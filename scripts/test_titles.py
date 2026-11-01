#!/usr/bin/env python3
"""Fail if any built page title is over 60 characters.

MONTH is an abbreviated month plus a year, as in "Sep 2026". Every month in
that format is checked, so a longer abbreviation cannot slip past a build that
happened to use a short one.
"""
import datetime
import html
import os
import re
import sys

LIMIT = 60
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


def main():
    errors = title_errors(os.path.join(ROOT, "dist"))
    if errors:
        raise SystemExit("title length check failed:\n- " + "\n- ".join(errors))
    count = len(rendered_titles(os.path.join(ROOT, "dist")))
    print(f"ok {count} titles are {LIMIT} characters or fewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
