"""Downloads the public pages of www.kami-skincare.com and rebuilds the
offline content snapshot in assets/data/ (products, FAQ, ingredients,
reviews, blog). Run this once before the first build, and again whenever
you want fresh texts:

    python3 tool/update_content.py

The snapshot is for private use only and is git-ignored on purpose, so the
shop's texts are never republished through this repository.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

SHOP = "https://www.kami-skincare.com"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "data")
HEADERS = {"User-Agent": "Mozilla/5.0 (KAMI private app content updater)"}

COLLECTIONS = [
    "neurodermitis", "anti-aging-pflege", "verbrennungen-narben-und-auas",
    "fur-die-pflege-juckender-kopfhaut-und-von-glatzen", "trockene-und-gereizte-haut",
    "alle-produkte",
]


def fetch(path, target):
    req = urllib.request.Request(SHOP + path, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as res, open(target, "wb") as f:
        f.write(res.read())
    time.sleep(0.3)  # be gentle with the shop


def main():
    site = tempfile.mkdtemp(prefix="kami_site_")
    print("Downloading into", site)
    fetch("/products.json?limit=250", os.path.join(site, "products.json"))
    for c in COLLECTIONS:
        fetch(f"/collections/{c}/products.json?limit=250", os.path.join(site, f"col_{c}.json"))
    for p in json.load(open(os.path.join(site, "products.json")))["products"]:
        fetch(f"/products/{p['handle']}", os.path.join(site, f"p_{p['handle']}.html"))
    fetch("/pages/faq-haufig-gestellte-fragen", os.path.join(site, "faq-haufig-gestellte-fragen.html"))
    fetch("/pages/inhaltsstoffe", os.path.join(site, "inhaltsstoffe.html"))
    fetch("/pages/kami-kundenbewertungen", os.path.join(site, "reviews.html"))
    fetch("/blogs/kami-blog.atom", os.path.join(site, "blog.atom"))
    for i in (1, 2, 3):
        fetch(f"/blogs/kami-blog?page={i}", os.path.join(site, f"blog_{i}.html"))
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "build_snapshot.py"), site, OUT], check=True)
    print("Snapshot written to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
