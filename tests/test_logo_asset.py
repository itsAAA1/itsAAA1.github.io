"""Check the static CoinMarketCap-ready branding asset without nonstdlib dependencies.

On-chain Pump.fun image equivalence remains a separate manual identity check.
"""
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MarketplaceLogo(unittest.TestCase):
    def test_200x200_transparent_png_asset(self):
        data = (ROOT / "logo-cmc-200.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(data[12:16], b"IHDR")
        self.assertEqual(struct.unpack_from(">II", data, 16), (200, 200))
        self.assertEqual(data[25], 6, "PNG must have RGBA alpha-capable color type")
        self.assertGreater(len(data), 5000)
        self.assertLess(len(data), 250000, "Listing logo should be compact")


if __name__ == "__main__":
    unittest.main()
