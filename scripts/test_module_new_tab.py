#!/usr/bin/env python3
"""Regression check: in-scope schedule links in module.html open in a new tab."""

from pathlib import Path

MODULE_LAYOUT = Path(__file__).resolve().parent.parent / "_layouts" / "module.html"

REQUIRED = [
    ("event title", '<a href="{{ event.url }}" target="_blank">{{ event.title }}</a>'),
    ("write button", '<a href="{{ event.html }}" target="_blank">'),
    ("guide button", '<a href="{{ event.guide }}" target="_blank">'),
    ("exam button", '<a href="{{ event.exam }}" target="_blank">'),
    ("practice button", '<a href="{{ event.practice }}" target="_blank">'),
    ("solutions button", '<a href="{{ event.solutions }}" target="_blank">'),
    ("notebook button", '<a href="{{ event.notebook }}" target="_blank">'),
]


def main() -> int:
    text = MODULE_LAYOUT.read_text(encoding="utf-8")
    errors = []
    for name, pattern in REQUIRED:
        if pattern not in text:
            errors.append(f'missing target="_blank" for {name}: expected {pattern!r}')
    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        return 1
    print('OK: all in-scope module links have target="_blank"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
