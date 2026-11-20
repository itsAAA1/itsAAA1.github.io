"""Regression tests for privacy-preserving, read-only Phantom account checker."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "wallet-check.html"
PUMP = "GGSqpEPw3WDvfqJRj6frvrTz1C2wcUz28Sgfdg2NNJiD"
SPL = "28fU8SDMKLXe8hqmdy9dxYNHeddm7xQRzkxK16JLUpi4"


class PhantomWalletChecker(unittest.TestCase):
    def test_page_is_present_and_identifies_both_expected_wallets(self):
        self.assertTrue(PAGE.is_file(), "Missing read-only wallet-check.html")
        html = PAGE.read_text(encoding="utf-8")
        self.assertIn(PUMP, html)
        self.assertIn(SPL, html)
        self.assertIn('href="verify-wallet.html"', html)
        self.assertIn('href="verify-spl-wallet.html"', html)

    def test_wallet_connection_does_not_sign_or_export_secrets(self):
        html = PAGE.read_text(encoding="utf-8")
        self.assertIn("window.phantom", html)
        self.assertIn("provider.connect(", html)
        self.assertIn("accountChanged", html)
        self.assertIn("toBase58()", html)
        for unsafe in ("signMessage(", "signTransaction(", "sendTransaction(",
                       "secretKey", "privateKey", "seedPhrase", "mnemonic",
                       "localStorage", "sessionStorage", "fetch(",
                       "sendBeacon(", "XMLHttpRequest"):
            self.assertNotIn(unsafe, html)

    def test_address_is_displayed_using_text_content(self):
        html = PAGE.read_text(encoding="utf-8")
        self.assertIn("addressEl.textContent", html)
        self.assertIn("expectedWallets", html)
        self.assertIn("noopener noreferrer", html)


if __name__ == "__main__":
    unittest.main()
