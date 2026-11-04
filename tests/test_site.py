"""Offline regression tests for the public VoltZilla GitHub Pages site."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "whitepaper.html")


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.images = []
        self.html_attrs = {}
        self.mains = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "html":
            self.html_attrs = attr
        if "id" in attr:
            self.ids.append(attr["id"])
        if tag == "a":
            self.links.append(attr)
        if tag == "img":
            self.images.append(attr)
        if tag == "main":
            self.mains += 1


class SiteIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {}
        for filename in PAGES:
            raw = (ROOT / filename).read_text(encoding="utf-8")
            doc = Document()
            doc.feed(raw)
            cls.pages[filename] = (raw, doc)

    def test_languages_and_landmarks(self):
        for filename, (raw, doc) in self.pages.items():
            with self.subTest(filename=filename):
                self.assertEqual(doc.html_attrs.get("lang"), "ar")
                self.assertEqual(doc.html_attrs.get("dir"), "rtl")
                self.assertEqual(doc.mains, 1, "Exactly one main landmark required")
                self.assertIn('id="main-content"', raw)
                self.assertIn('href="#main-content"', raw)
                self.assertEqual(raw.count("</main>"), 1)

    def test_unique_ids_and_valid_internal_links(self):
        for filename, (_, doc) in self.pages.items():
            with self.subTest(filename=filename):
                duplicates = [key for key, count in Counter(doc.ids).items() if count > 1]
                self.assertEqual(duplicates, [], "Duplicate HTML ids")
                for link in doc.links:
                    href = link.get("href", "")
                    self.assertTrue(href and href != "#", f"Empty link in {filename}")
                    if href.startswith("#"):
                        self.assertIn(href[1:], doc.ids, f"Missing {href} in {filename}")
                    elif href.startswith(("https://", "http://")):
                        self.assertEqual(urlsplit(href).scheme, "https", "Insecure external link")
                    else:
                        path = href.split("#", 1)[0].split("?", 1)[0]
                        self.assertTrue((ROOT / path).is_file(), f"Broken link {href} in {filename}")

    def test_external_tabs_are_safe(self):
        for filename, (_, doc) in self.pages.items():
            for link in doc.links:
                if link.get("target") == "_blank":
                    rel = set((link.get("rel") or "").split())
                    self.assertIn("noopener", rel, f"Missing noopener in {filename}")
                    self.assertIn("noreferrer", rel, f"Missing noreferrer in {filename}")

    def test_images_and_favicons(self):
        for filename, (raw, doc) in self.pages.items():
            for img in doc.images:
                self.assertTrue(img.get("alt", "").strip(), f"Missing alt in {filename}")
                self.assertTrue(img.get("width"), f"Missing width in {filename}")
                self.assertTrue(img.get("height"), f"Missing height in {filename}")
                image_path = img.get("src", "")
                self.assertTrue((ROOT / image_path).is_file(), f"Missing image {image_path}")
            self.assertIn('href="favicon.svg"', raw)
        self.assertLess((ROOT / "favicon.svg").stat().st_size, 4096)

    def test_mobile_navigation_and_resilient_rendering(self):
        raw = self.pages["index.html"][0]
        self.assertIn('<details class="mobile-nav">', raw)
        self.assertIn('<div class="mobile-nav-panel">', raw)
        self.assertIn('.mobile-nav{display:block}', raw)
        self.assertIn('nav{position:sticky', raw)
        self.assertIn('.ticker{position:relative', raw)
        self.assertIn('.fade-in{opacity:1;', raw)
        self.assertNotIn("new IntersectionObserver", raw)
        self.assertIn('a:focus-visible', raw)
        self.assertIn('prefers-reduced-motion:reduce', raw)

    def test_metadata_and_historical_whitepaper(self):
        homepage = self.pages["index.html"][0]
        paper = self.pages["whitepaper.html"][0]
        self.assertIn('rel="canonical" href="https://itsaaa1.github.io/"', homepage)
        self.assertIn('rel="canonical" href="https://itsaaa1.github.io/whitepaper.html"', paper)
        self.assertIn('name="robots" content="noindex, follow"', paper)
        self.assertIn('class="table-scroll"', paper)
        self.assertEqual(paper.count('class="table-scroll"'), 2)
        self.assertEqual(paper.count('data-label="'), paper.count("<td"), "Every data cell must have a mobile label")
        self.assertIn('.table-scroll{overflow:visible}', paper)
        self.assertIn('.wp-table td::before{content:attr(data-label)', paper)
        self.assertIn('.wp-table tr{display:block', paper)
        self.assertNotIn("TO THE MOON", homepage)
        self.assertIn("DHxStA9nRq6DdhBKT89s38fpxD9wE7MtyMn9HMuWeyN9", homepage)
        self.assertIn("DHxStA9nRq6DdhBKT89s38fpxD9wE7MtyMn9HMuWeyN9", paper)
        self.assertIn("صلاحية سك توكنات إضافية", homepage)
        self.assertIn("سلطة سك مزيد من العملات: مفعّلة", paper)
        self.assertIn("توكن مختلف بمعروض يقارب المليار", paper)

    def test_sitemap_and_robots(self):
        sitemap = ET.parse(ROOT / "sitemap.xml")
        urls = [n.text for n in sitemap.iter() if n.tag.endswith("loc")]
        self.assertIn("https://itsaaa1.github.io/", urls)
        self.assertNotIn("https://itsaaa1.github.io/whitepaper.html", urls)
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://itsaaa1.github.io/sitemap.xml", robots)
        self.assertNotIn("Disallow: /whitepaper.html", robots)


if __name__ == "__main__":
    unittest.main()
