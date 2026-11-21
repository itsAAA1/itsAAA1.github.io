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
PAGES = ("index.html", "whitepaper.html", "status.html", "whitepaper-current.html", "faq.html", "support.html", "legal.html", "market.html", "wallet.html", "roadmap.html", "verify-wallet.html", "verify-spl-wallet.html", "proof.html")
# X account the owner stated on 5 Nov 2026. Not proven official: @VoltZillaSOL is in the GDY metadata.
OWNER_STATED_X = "https://x.com/voltzillasol1"
PUMPFUN_COIN = "https://pump.fun/coin/GDYcemcZozG9ijhEZioRLRgNMtoxh1BBuV7nvdf1pump"
PRIMARY_MINT = "GDYcemcZozG9ijhEZioRLRgNMtoxh1BBuV7nvdf1pump"
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
    "✅ المرحلة 1",
    "إطلاق التوكن على Pump.fun",
    "إطلاق GDY في مايو 2026",
    "65,000 TPS",
    "HOLD STRONG",
    # The official X account is undecided; no page may call either account official.
    "الحساب المعتمد",
    "حساب X المعتمد",
    "حساب X الرسمي هو",
]
FORBIDDEN_REGEX = [
    (r"ضريبة (?:الشراء|البيع|المعاملات)</td><td>\s*0\s*%", "zero-tax table value"),
    (r'stat-number">\s*0\s*%', "zero-tax stat"),
    (r"إجمالي العرض</td><td>\s*[\d,]{6,}", "unverified supply figure"),
]
REQUIRED_TEXT = {
    "index.html": ["GDYcemcZozG9ijhEZioRLRgNMtoxh1BBuV7nvdf1pump", "4 أبريل 2026", "لا تشترِ", "@voltzillasol1", "@VoltZillaSOL", "لم يُحسم", "لم يُقدَّم بعد"],
    "whitepaper.html": ["قيد التحقق", "لم تثبت صلته بمالك المشروع", "لم يُقدَّم أي طلب بعد", "بحسب مسودة سابقة غير معتمدة"],
    "status.html": [PRIMARY_MINT, "لم تثبت صلته بمالك المشروع", "لا تشترِ"],
    "whitepaper-current.html": [PRIMARY_MINT, "Token-2022", "4 أبريل 2026", "مخاطر", "لم تُقدَّم بعد"],
    "faq.html": [PRIMARY_MINT, "لم تثبت صلته بمالك المشروع", "لا توجد موافقة"],
    "support.html": ["github.com/itsAAA1/VoltZilla/issues/new", "رسالة واضحة غير مالية"],
    "legal.html": ["وزارة المالية", "2018", "2019", "لم يُنجز رأي قانوني مستقل"],
    "market.html": [PRIMARY_MINT, "DEX Screener", "حجم 24 ساعة", "غير مضمون الحداثة", "geckoterminal.com/solana/pools/6PpZaXsSnXCwm37W1PkMtmG1kCLjYNXk95eLoHMsFXBk?embed=1"],
    "wallet.html": [PRIMARY_MINT, "getTokenAccountsByOwner", "0.395563648", "7,005,921.840554"],
    "roadmap.html": ["المرحلة 1", "إثبات", "السيولة", "MVX مشروع مستقل"],
    "verify-wallet.html": ["GDYcemcZozG9ijhEZioRLRgNMtoxh1BBuV7nvdf1pump", "GGSqpEPw3WDvfqJRj6frvrTz1C2wcUz28Sgfdg2NNJiD", "crypto.subtle.verify"],
    "proof.html": ["28fU8SDMKLXe8hqmdy9dxYNHeddm7xQRzkxK16JLUpi4", "vXZ+kxA5WCr9lPS/VZzvUBMctxE1zP+rAcIkjBVpwY5K7tt3W6rzBhV/+bahSaZPxjfdph/CTLtsPNmIvquODQ==", "crypto.subtle.verify", "ليس معاملة", "لم يُتحقق بعد"],
    "verify-spl-wallet.html": ["DHxStA9nRq6DdhBKT89s38fpxD9wE7MtyMn9HMuWeyN9", "28fU8SDMKLXe8hqmdy9dxYNHeddm7xQRzkxK16JLUpi4", "crypto.subtle.verify"],
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
        if OWNER_STATED_X not in p.hrefs:
            errors.append(f"{name}: missing owner-confirmed X link")
        for href in p.hrefs:
            if href.startswith("http"):
                if any(s in href for s in FORBIDDEN_SOCIAL):
                    errors.append(f"{name}: unconfirmed social link {href}")
                if "x.com/" in href and href.rstrip("/") != OWNER_STATED_X:
                    errors.append(f"{name}: unexpected X link {href}")
                if "pump.fun/coin/" in href and href.rstrip("/") != PUMPFUN_COIN:
                    errors.append(f"{name}: unrelated Pump.fun token contract link {href}")
        if name == "market.html":
            if 'p.baseToken.address===MINT' not in text or 'p.chainId==="solana"' not in text:
                errors.append("market.html: price selection must match the exact mint and network")
            if 'p.volume.h24!==null' not in text:
                errors.append("market.html: missing-volume values must not silently display zero")
        if name in ("verify-wallet.html", "verify-spl-wallet.html"):
            if any(x in text for x in ("sendTransaction", "signTransaction", "exportSecretKey", "secretKey", "seedPhrase")):
                errors.append(f"{name}: signing challenge must not have transfer or key export methods")
            if "crypto.randomUUID()" not in text or "crypto.subtle.verify" not in text or "provider.signMessage" not in text:
                errors.append(f"{name}: secure fresh challenge / signature verification missing")
            if 'id="phantom-open"' not in text or "https://phantom.app/ul/browse/" not in text:
                errors.append(f"{name}: iPhone must offer a wallet-app deep link (not Safari signing)")
            if "encodeURIComponent(window.location.href)" not in text or "encodeURIComponent(window.location.origin)" not in text:
                errors.append(f"{name}: Phantom universal link must be generated for the same site and referrer origin")
            if "الحساب المتصل: " not in text or "المحفظة المطلوبة: " not in text:
                errors.append(f"{name}: account mismatch must display actual and expected Solana addresses")
            if "connectionResult?.publicKey || provider.publicKey" not in text:
                errors.append(f"{name}: provider.connect() account return fallback missing")
            if 'id="diagnose"' not in text or "diagnosticBtn.addEventListener" not in text or "signMessage(true)" not in text:
                errors.append(f"{name}: mobile wallet diagnostic signing button must be wired")
            if 'const matchesExpectedWallet = signer === expectedWallet;' not in text or 'if (!diagnosticOnly && !matchesExpectedWallet)' not in text:
                errors.append(f"{name}: normal ownership proof must deny mismatched wallet while diagnostic can sign")
            if '"Matches expected wallet: " + matchesExpectedWallet' not in text or 'copyBtn.disabled = true;' not in text:
                errors.append(f"{name}: diagnostic signature must label mismatch and not expose publishable proof")
            if '<script src=' in text:
                errors.append(f"{name}: do not load remote scripts into signing page")
        if name == "wallet.html":
            if not all(x in text for x in ("getBalance", "getTokenAccountsByOwner", "GGSqpEPw3WDvfqJRj6frvrTz1C2wcUz28Sgfdg2NNJiD")):
                errors.append("wallet.html: public read-only balance verification missing")
            if any(x in text for x in ("signTransaction", "sendTransaction", "secretKey", "seedPhrase", "mnemonic")):
                errors.append("wallet.html: prohibited signing/key handling code detected")
        if name == "index.html":
            for old in ("&#x1F525; جاري", 'class="phase-num done"', 'class="roadmap-phase active"'):
                if old in text:
                    errors.append(f"{name}: outdated status {old}")
            for platform in ("CoinGecko", "CoinMarketCap"):
                pattern = rf'{platform} <span[^>]*></span></div><div[^>]*>لم يُقدَّم بعد</div>'
                if not re.search(pattern, text):
                    errors.append(f"{name}: unverified listing status for {platform}")
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
            if name not in ("whitepaper.html", "status.html", "faq.html") or "لم تثبت صلته بمالك المشروع" not in text:
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
