#!/usr/bin/env python3
"""Shareable calculator query parsing."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calc_links

MODELS = ["kling-3-0", "wan-3-0", "veo-3-1"]
PLANS = {
    "hf-starter": {"platform": "Higgsfield"},
    "mag-premium": {"platform": "Magnific"},
    "krea-pro-monthly": {"platform": "Krea"},
}
RESOLUTIONS = ["480p", "720p", "1080p"]


def parse(raw):
    return calc_links.parse_calc_params(raw, MODELS, PLANS, RESOLUTIONS)


def main():
    got = parse({"model": "kling-3-0", "seconds": "10"})
    assert got["model"] == "kling-3-0" and got["seconds"] == 10, got
    assert "plan" not in parse({"model": "not-a-model", "seconds": "0", "audio": "loud"})
    assert parse({"model": "sora"}) == {}
    assert parse({"seconds": "foo", "sec": "8"})["seconds"] == 8
    assert parse({"resolution": "720P"})["resolution"] == "720p"
    assert parse({"res": "not listed"})["resolution"] == "not listed"
    assert "resolution" not in parse({"resolution": "12k"})
    assert parse({"audio": "on"})["audio"] == "with"
    assert parse({"audio": "off"})["audio"] == "without"
    assert "audio" not in parse({"audio": "maybe"})
    assert parse({"input": "t2v"})["input"] == "t2v"
    assert "input" not in parse({"input": "song"})
    assert parse({"plan": "hf-starter"})["plan"] == "hf-starter"
    assert "plan" not in parse({"plan": "nope"})
    assert parse({"provider": "magnific"})["plan"] == "mag-premium"
    assert parse({"platform": "Krea"})["plan"] == "krea-pro-monthly"
    assert "plan" not in parse({"provider": "fal"})
    both = parse({"plan": "hf-starter", "provider": "Magnific"})
    assert both["plan"] == "hf-starter" and "provider" not in both, both
    same = parse({"plan": "mag-premium", "provider": "Magnific"})
    assert same["provider"] == "Magnific"
    assert parse({"used": "40"})["used"] == 40
    assert "used" not in parse({"used": "0"})
    assert "used" not in parse({"used": "101"})
    print("ok calc params")


if __name__ == "__main__":
    main()
