#!/usr/bin/env python3
"""Tag VidFare links with UTM parameters so GoatCounter can tell channels apart.

Convention (docs/analytics.md):
  source      medium
  reddit      social
  x           social
  newsletter  email
  directory   referral
  utm_campaign is a slug: lowercase a-z, 0-9 and '-' (e.g. cheapest-kling-nov26).

GoatCounter reads utm_campaign (Campaigns widget) and utm_source (Referrers)
from the page view. vf-events.js also sends campaign/<source>/<medium>/<campaign>
so the medium is kept.

  python3 scripts/utm.py https://vidfare.com/deals/ --source reddit --medium social --campaign "Black Friday 2026"
  -> https://vidfare.com/deals/?utm_source=reddit&utm_medium=social&utm_campaign=black-friday-2026
"""
import argparse
import re
import sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

SOURCES = {
    "reddit": "social",
    "x": "social",
    "newsletter": "email",
    "directory": "referral",
}
SITE_HOSTS = {"vidfare.com", "www.vidfare.com"}
UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "campaign", "ref", "src", "source")


def slugify(text, limit=60):
    s = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return s[:limit].strip("-")


def utm_url(url, source, campaign, medium=None, content=None, any_host=False):
    """Return url with utm_source, utm_medium, utm_campaign (and utm_content) set.

    Raises ValueError for an unknown source, a medium that does not match the
    source, an empty campaign, or a non-VidFare URL (unless any_host=True).
    Existing utm_* / ref / campaign parameters are replaced; others are kept.
    """
    source = (source or "").strip().lower()
    if source not in SOURCES:
        raise ValueError(f"unknown source {source!r}; use one of: {', '.join(sorted(SOURCES))}")
    want = SOURCES[source]
    medium = (medium or want).strip().lower()
    if medium != want:
        raise ValueError(f"source {source!r} uses medium {want!r}, not {medium!r}")
    slug = slugify(campaign)
    if not slug:
        raise ValueError("campaign is required (it becomes a slug like cheapest-kling-nov26)")
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError(f"not an absolute http(s) URL: {url!r}")
    if not any_host and parts.hostname.lower() not in SITE_HOSTS:
        raise ValueError(f"{parts.hostname} is not vidfare.com (pass any_host=True / --any-host to tag it anyway)")
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in UTM_KEYS]
    pairs += [("utm_source", source), ("utm_medium", medium), ("utm_campaign", slug)]
    if content:
        c = slugify(content)
        if c:
            pairs.append(("utm_content", c))
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", urlencode(pairs), parts.fragment))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Add VidFare UTM parameters to a link.")
    ap.add_argument("url")
    ap.add_argument("--source", required=True, choices=sorted(SOURCES))
    ap.add_argument("--medium", help="defaults to the medium for the source")
    ap.add_argument("--campaign", required=True, help="free text, slugified")
    ap.add_argument("--content", help="optional utm_content (which post or placement)")
    ap.add_argument("--any-host", action="store_true", help="allow a non-vidfare.com URL")
    args = ap.parse_args(argv)
    try:
        print(utm_url(args.url, args.source, args.campaign, args.medium, args.content, args.any_host))
    except ValueError as err:
        print(f"utm.py: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
