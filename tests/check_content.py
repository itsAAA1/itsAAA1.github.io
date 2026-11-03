#!/usr/bin/env python3
"""Deterministic offline content checks for the VoltZilla static site.

Run from the repository root:  python3 tests/check_content.py
No network access is used. Exits non-zero on any failure.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ("index.html", "whitepaper.html")
OFFICIAL_X = "https://x.com/voltzillasol1"
FORBIDDEN_SOCIAL = ("t.me/", "telegram.me/", "discord.gg/", "discord.com/invite", "twitter.com/", "instagram.com/", "youtube.com/", "facebook.com/")

# Unsupported assertions that must not reappear (token address/tax/distribution are unconfirmed).
FORBIDDEN_TEXT = [
    "صفر ضرائب",
    "لا ضريبة على الشراء ولا على البيع",
    "بدون ضرائب",
    "كل توكن في يد المجتمع",
    "الشفافية الكاملة",
    "لا توجد ضرائب",
    "متاح للشراء العام",
    "افتح Pump.fun",
    "ابحث عن VZLA",
    "اضغط Buy",
    "كيف تشتري",
    "اشترِ SOL من أي بورصة",
]
FORBIDDEN_REGEX = [
    (r"ضريبة (?:الشراء|البيع|المعاملات)</td><td>\s*0\s*%", "zero-tax table value"),
    (r'stat-number">\s*0\s*%', "zero-tax stat"),
    (r"(?:https?://)?(?:www\.)?pump\.fun/coin/", "pump.fun coin link"),
    (r"إجمالي العرض</td><td>\s*[\d,]{6,}", "unverified supply figure"),
]
REQUIRED_TEXT = {
    "index.html": ["قيد التحقق", "غير معتمد", "لا تشترِ", "@voltzillasol1"],
    "whitepaper.html": ["قيد التحقق", "لم تثبت صلته بمالك المشروع"],
}
# The previously published address is flagged as unverified; it may only appear in the whitepaper with that label.
OLD_ADDRESS = "JBaHDseUdFEVbAik7rojwC8ZZ8EjyBi1qQPoK9tLpump"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.opens, self.closes = [], 0, 0

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.opens += 1
            self.hrefs.append(dict(attrs).get("href", "") or "")

    def handle_endtag(self, tag):
        if tag == "a":
            self.closes += 1


def main():
    errors = []
    for name in PAGES:
        text = (ROOT / name).read_text(encoding="utf-8")
        p = Links()
        p.feed(text)
        if p.opens != p.closes:
            errors.append(f"{name}: unbalanced <a> tags ({p.opens}/{p.closes})")
        if OFFICIAL_X not in p.hrefs:
            errors.append(f"{name}: missing owner-confirmed X link")
        for href in p.hrefs:
            if href.startswith("http"):
                if any(s in href for s in FORBIDDEN_SOCIAL):
                    errors.append(f"{name}: unconfirmed social link {href}")
                if "x.com/" in href and href.rstrip("/") != OFFICIAL_X:
                    errors.append(f"{name}: unexpected X link {href}")
                if "pump.fun" in href:
                    errors.append(f"{name}: purchase/launch-platform link {href}")
        for s in FORBIDDEN_TEXT:
            if s in text:
                errors.append(f"{name}: forbidden unsupported text: {s!r}")
        for rx, label in FORBIDDEN_REGEX:
            if re.search(rx, text):
                errors.append(f"{name}: forbidden pattern ({label}): {rx}")
        for s in REQUIRED_TEXT.get(name, []):
            if s not in text:
                errors.append(f"{name}: required text missing: {s!r}")
        if OLD_ADDRESS in text:
            if name != "whitepaper.html" or "لم تثبت صلته بمالك المشروع" not in text:
                errors.append(f"{name}: old address present without unverified label")
        print(f"{name}: {len(p.hrefs)} links checked")
    # The branding assets must remain in place.
    for asset in ("logo.png", "favicon.png"):
        if not (ROOT / asset).is_file():
            errors.append(f"missing asset {asset}")
    if 'src="logo.png"' not in (ROOT / "index.html").read_text(encoding="utf-8"):
        errors.append("index.html: logo reference removed")
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: all content checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
