"""Regression checks for a user-signed, read-only VoltZilla wallet proof and honest token metadata."""
from pathlib import Path
from html.parser import HTMLParser
import unittest

ROOT = Path(__file__).resolve().parents[1]
MINT = "GDYcemcZozG9ijhEZioRLRgNMtoxh1BBuV7nvdf1pump"
WALLET = "GGSqpEPw3WDvfqJRj6frvrTz1C2wcUz28Sgfdg2NNJiD"
RAYDIUM = "3cPWF3eKjcq4Y8d2oVXDRaN8ipKBHuyK1uYWY4GT7ray"


class WalletProof(unittest.TestCase):
    def test_safe_wallet_message_verification_is_present(self):
        html = (ROOT / "verify-wallet.html").read_text(encoding="utf-8")
        self.assertIn(MINT, html)
        self.assertIn(WALLET, html)
        self.assertIn("signMessage(", html)
        self.assertIn("crypto.subtle.verify", html)
        self.assertIn("Ed25519", html)
        self.assertIn("crypto.randomUUID()", html)
        self.assertIn("Expires UTC:", html)
        self.assertIn('"Proof of wallet control only; NOT a transaction or spending authorization"', html)
        self.assertIn('"Purpose: " + (diagnosticOnly ?', html)
        self.assertIn("if (!diagnosticOnly && !matchesExpectedWallet)", html)
        self.assertNotIn("signTransaction(", html)
        self.assertNotIn("sendTransaction(", html)
        self.assertNotIn("secretKey", html)
        self.assertNotIn("privateKey", html)
        self.assertIn("window.solana", html)
        self.assertIn("window.phantom", html)

    def test_phantom_diagnostic_never_becomes_an_owner_proof(self):
        """A test signature from a different iPhone wallet must not assert token ownership."""
        for name in ("verify-wallet.html", "verify-spl-wallet.html"):
            with self.subTest(name=name):
                html = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn('id="diagnose"', html)
                self.assertIn('diagnosticBtn.addEventListener("click", () => signMessage(true))', html)
                self.assertIn("if (!diagnosticOnly && !matchesExpectedWallet)", html)
                self.assertIn('copyBtn.disabled = true;', html)
                self.assertIn('proofEl.value = "";', html)
                self.assertIn("Technical signing diagnostic only; NOT VoltZilla ownership proof", html)
                self.assertIn("crypto.subtle.verify", html)
                self.assertNotIn("sendTransaction(", html)
                self.assertNotIn("signTransaction(", html)
                self.assertNotIn("secretKey", html)

    def test_other_mints_and_inactive_modes_are_not_sold_as_active(self):
        html = (ROOT / "status.html").read_text(encoding="utf-8")
        self.assertIn(RAYDIUM, html)
        self.assertIn("Mayhem", html)
        self.assertIn("Holder Rewards", html)
        self.assertIn("Cashback", html)
        self.assertIn("غير مُفعّل", html)
        self.assertIn('href="verify-wallet.html"', html)
        self.assertIn("لم يُتحقق", html)


if __name__ == "__main__":
    unittest.main()
