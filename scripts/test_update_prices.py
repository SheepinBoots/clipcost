#!/usr/bin/env python3
"""Exit-code rules for the daily price check."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_prices as up


def main():
    assert up.exit_code([], False) == 0
    applied = {"status": "changed", "applied": True}
    assert up.exit_code([applied, dict(applied)], False) == 0
    assert up.exit_code([{"status": "missing"}], False) == 1
    assert up.exit_code([applied, {"status": "missing"}], False) == 1
    assert up.exit_code([{"status": "changed"}], False) == 1
    assert up.exit_code([{"status": "deal_candidate"}], False) == 1
    assert up.exit_code([], True) == 2
    assert up.exit_code([{"status": "missing"}], True) == 2
    print("ok")


if __name__ == "__main__":
    main()
