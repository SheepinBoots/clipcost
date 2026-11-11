#!/usr/bin/env python3
"""Cookie-free GoatCounter event markup for the built pages.

build_site.py calls annotate() on every page it writes. It adds data-vf-*
attributes to outbound, affiliate, sponsor and /advertise/ links and to the
newsletter form. src/vf-events.js reads those attributes on click/submit and
sends one GoatCounter event (goatcounter.count with event:true). Nothing is
stored in the browser: no cookies, no localStorage, no sessionStorage.

Event paths (see docs/analytics.md):
  newsletter-signup/<page>
  outbound/<vendor>/<page>
  outbound-affiliate/<vendor>/<page>
  sponsor-click/<slot>/<page>
  advertise-cta/<cta>/<page>
  campaign/<source>/<medium>/<campaign>
"""
import json
import re
from urllib.parse import urlsplit, parse_qsl

SCRIPT_PATH = "/vf-events.js"
SITE_HOSTS = {"vidfare.com", "www.vidfare.com"}
# Shared hosts that a deal can cite but that are not the vendor itself.
SHARED_HOSTS = {"x.com", "twitter.com", "openrouter.ai", "github.com", "youtube.com", "reddit.com", "discord.gg", "discord.com"}
HOSTS_PLACEHOLDER = "/*VF_HOSTS*/{}"


def slug(text, limit=60):
    """Lowercase a-z0-9 words joined by '-'. Matches vfSlug() in vf-events.js."""
    s = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return s[:limit].strip("-")


def page_slug(path):
    """'/' -> home, '/models/kling-3-0/' -> models-kling-3-0, '/404.html' -> 404."""
    p = (path or "/").split("?")[0].split("#")[0]
    p = re.sub(r"(index)?\.html$", "", p).strip("/")
    return slug(p.replace("/", "-"), 80) or "home"


def _host(url):
    host = (urlsplit(url or "").hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def host_map(rows, deals):
    """hostname -> vendor slug, from prices.json rows and deals.json deals."""
    out = {}
    for r in rows or []:
        h = _host(r.get("source_url"))
        if h and h not in SHARED_HOSTS and r.get("platform"):
            out.setdefault(h, slug(r["platform"]))
    for d in deals or []:
        for key in ("link_url", "source_url"):
            h = _host(d.get(key))
            if h and h not in SHARED_HOSTS and d.get("vendor"):
                out.setdefault(h, slug(d["vendor"]))
    return dict(sorted(out.items()))


def vendor_for(url, hosts):
    """Vendor slug for a URL: exact host, then a parent domain, then the host itself."""
    h = _host(url)
    if not h:
        return ""
    if h in hosts:
        return hosts[h]
    parts = h.split(".")
    for i in range(1, len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in hosts:
            return hosts[parent]
    return slug(h)


def vendor_known(url, hosts):
    h = _host(url)
    return bool(h) and (h in hosts or any(h.endswith("." + k) for k in hosts))


def is_affiliate(href, rel, in_sponsor_slot):
    """Affiliate = the build's existing marker (rel=sponsored) or a referral
    parameter (fpr=). Paid sponsor slots also use rel=sponsored, so links inside
    aside[data-sponsor] are sponsor clicks, not affiliate clicks."""
    if in_sponsor_slot:
        return False
    if "sponsored" in (rel or "").split():
        return True
    q = dict(parse_qsl(urlsplit(href or "").query))
    return "fpr" in q


def js_source(src_text, hosts):
    """The deployed script: src/vf-events.js with the vendor host map filled in."""
    if HOSTS_PLACEHOLDER not in src_text:
        raise SystemExit("src/vf-events.js is missing the " + HOSTS_PLACEHOLDER + " placeholder")
    return src_text.replace(HOSTS_PLACEHOLDER, json.dumps(hosts, separators=(",", ":"), sort_keys=True))


def script_tag(path, root=lambda p: p):
    return f'<script defer src="{root(SCRIPT_PATH)}" data-vf-page="{page_slug(path)}"></script>'


_SKIP = re.compile(r"<script\b.*?</script>|<!--.*?-->", re.S | re.I)
_ASIDE = re.compile(r'<aside\b[^>]*\bdata-sponsor="([^"]*)"[^>]*>.*?</aside>', re.S | re.I)
_A = re.compile(r"<a\b[^>]*>", re.I)
_ATTR = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"')
_FORM = re.compile(r"<form\b[^>]*>", re.I)


def _spans(rx, text):
    return [(m.start(), m.end(), m) for m in rx.finditer(text)]


def _inside(pos, spans):
    for a, b, m in spans:
        if a <= pos < b:
            return m
    return None


def _unescape(v):
    return v.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'").replace("&#39;", "'")


def annotate(doc, path, hosts, advertise_path="/advertise/", model=None):
    """Add data-vf-* attributes to links and newsletter forms in a built page.

    Only attributes are added, so the rendered layout does not change.
    Markup inside <script> blocks (JSON-LD, client templates) is left alone;
    vf-events.js classifies client-rendered links at click time instead.
    """
    start = doc.find("<body")
    if start == -1:
        return doc
    skip = _spans(_SKIP, doc)
    asides = _spans(_ASIDE, doc)
    footer_at = doc.find("<footer")
    on_advertise = page_slug(path) == page_slug(advertise_path)
    out = []
    last = 0

    def add(tag, attrs):
        extra = "".join(f' {k}="{v}"' for k, v in attrs.items() if v)
        return tag[:-1].rstrip("/").rstrip() + extra + (" />" if tag.endswith("/>") else ">") if extra else tag

    for m in sorted(list(_A.finditer(doc, start)) + list(_FORM.finditer(doc, start)), key=lambda x: x.start()):
        if _inside(m.start(), skip):
            continue
        tag = m.group(0)
        if "data-vf-" in tag:
            continue
        attrs = {k.lower(): _unescape(v) for k, v in _ATTR.findall(tag)}
        new = {}
        if tag.lower().startswith("<form"):
            action = attrs.get("action", "")
            if "data-sv-form" in tag or "formkit" in attrs.get("class", "") or "kit.com/forms" in action:
                new["data-vf-event"] = "newsletter-signup"
        else:
            href = attrs.get("href", "").strip()
            rel = attrs.get("rel", "")
            aside = _inside(m.start(), asides)
            in_footer = footer_at != -1 and m.start() > footer_at
            if aside is not None:
                slot = slug(aside.group(1)) or "unknown"
                if href.rstrip("/").endswith(advertise_path.rstrip("/")):
                    new["data-vf-cta"] = "sponsor-slot-" + slot
                else:
                    new["data-vf-sponsor"] = slot
            elif href and urlsplit(href).path.rstrip("/") == advertise_path.rstrip("/") and not urlsplit(href).hostname:
                new["data-vf-cta"] = "footer-link" if in_footer else "inline-link"
            elif href.lower().startswith("mailto:") and (on_advertise or "sponsorship" in href.lower()):
                new["data-vf-cta"] = "email" if on_advertise else "sponsorship-email"
            elif (href.lower().startswith(("http://", "https://")) and _host(href) not in SITE_HOSTS
                  and (vendor_known(href, hosts) or is_affiliate(href, rel, False))):
                # Known vendor/deal hosts only. Other external links (directory
                # badges, docs) are still counted by vf-events.js by hostname.
                new["data-vf-vendor"] = vendor_for(href, hosts) or "unknown"
                if model:
                    new["data-vf-model"] = slug(model)
                if is_affiliate(href, rel, False):
                    new["data-vf-affiliate"] = "1"
        if new:
            out.append(doc[last:m.start()])
            out.append(add(tag, new))
            last = m.end()
    out.append(doc[last:])
    return "".join(out)
