"""Builds the offline content snapshot for the private KAMI app.

Reads the HTML/JSON files downloaded into the site directory (argv[1]) and
writes JSON files into the app's assets/data directory (argv[2]).
Images are NOT copied - the app loads them from Shopify's CDN at runtime.
"""
import html
import json
import os
import re
import sys

SITE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def read(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as f:
        return f.read()


def clean(fragment):
    fragment = re.sub(r"<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"</p>|</li>|</h\d>", "\n", fragment)
    text = html.unescape(re.sub(r"<[^>]+>", "", fragment))
    lines = [re.sub(r"[ \t​\xa0]+", " ", l).strip() for l in text.split("\n")]
    return "\n".join(l for l in lines if l)


def main_lines(page):
    b = page[page.find("<main"):page.find("</main>")]
    b = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", "", b, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", b))
    return [re.sub(r"[\s​\xa0]+", " ", l).strip() for l in t.split("\n") if l.strip()]


# ---------- products ----------
products = json.loads(read("products.json"))["products"]
collections = {}
for f in os.listdir(SITE):
    if f.startswith("col_"):
        handle = f[4:-5]
        collections[handle] = [p["handle"] for p in json.loads(read(f))["products"]]

# Pages that are not Shopify collections get curated product lists.
collections["psoriasis"] = ["psoriasis-set", "kami-sos-hautpflegeol-dropper",
                            "kami-sos-hautpflege-balsam", "kami-2-phasen-pflegespray"]
collections["narbenpflege"] = ["narbenpflege-set", "kami-sos-hautpflege-balsam",
                               "kami-sos-hautpflegeol-dropper"]

out_products = []
for p in products:
    extra = {"subtitle": "", "ingredients": "", "usage": "", "reviewCount": 0}
    fname = f"p_{p['handle']}.html"
    if os.path.exists(os.path.join(SITE, fname)):
        L = main_lines(read(fname))
        for i, l in enumerate(L):
            m = re.match(r"^(\d+) Bewertung", l)
            if m and not extra["reviewCount"]:
                extra["reviewCount"] = int(m.group(1))
                if i + 2 < len(L):
                    extra["subtitle"] = L[i + 2] if L[i + 1] == p["title"] else ""

        def section(start, ends):
            if start not in L:
                return ""
            i = L.index(start) + 1
            buf = []
            while i < len(L) and L[i] not in ends:
                buf.append(L[i])
                i += 1
            return "\n".join(buf)

        stops = {"Zufriedenheitsgarantie", "Anwendung", "Inhaltsstoffe", "Eine Frage stellen"}
        extra["ingredients"] = section("Inhaltsstoffe", stops)
        extra["usage"] = section("Anwendung", stops)
    if extra["subtitle"].upper().startswith("DERZEIT"):
        extra["notice"], extra["subtitle"] = extra["subtitle"], ""
    out_products.append({
        "id": p["id"],
        "handle": p["handle"],
        "title": p["title"],
        "description": clean(p["body_html"] or ""),
        "images": [i["src"] for i in p["images"]],
        "variants": [{"id": v["id"], "title": v["title"], "price": v["price"],
                      "compareAtPrice": v["compare_at_price"], "available": v["available"]}
                     for v in p["variants"]],
        **extra,
    })

with open(os.path.join(OUT, "products.json"), "w", encoding="utf-8") as f:
    json.dump({"products": out_products, "collections": collections}, f, ensure_ascii=False, indent=1)

# ---------- FAQ ----------
faq_html = read("faq-haufig-gestellte-fragen.html")
faq = []
for m in re.finditer(r'<details[^>]*>\s*<summary class="accordion-details__summary[^"]*"[^>]*>(.*?)</summary>(.*?)</details>', faq_html, re.S):
    q, a = clean(m.group(1)), clean(m.group(2))
    if q in ("KAMI", "Menü", "Service"):
        continue
    if q and a and q not in [x["q"] for x in faq]:
        faq.append({"q": q.replace("​", ""), "a": a})
with open(os.path.join(OUT, "faq.json"), "w", encoding="utf-8") as f:
    json.dump(faq, f, ensure_ascii=False, indent=1)

# ---------- ingredients ----------
L = main_lines(read("inhaltsstoffe.html"))
ingredients = []
end = L.index("100% Natur mit medizinischem Know-How") if "100% Natur mit medizinischem Know-How" in L else len(L)
i = 1
while i + 1 < end:
    ingredients.append({"name": L[i], "text": L[i + 1]})
    i += 2
with open(os.path.join(OUT, "ingredients.json"), "w", encoding="utf-8") as f:
    json.dump(ingredients, f, ensure_ascii=False, indent=1)

# ---------- reviews (Judge.me, server rendered) ----------
rv = read("reviews.html")
reviews = []
for block in re.split(r"<div class='jdgm-rev jdgm-divider-top'", rv)[1:]:
    def g(pat):
        m = re.search(pat, block, re.S)
        return clean(m.group(1)) if m else ""
    score = re.search(r"data-score='(\d)'", block)
    date = re.search(r"jdgm-rev__timestamp[^>]*data-content='([^']+)'", block)
    reviews.append({
        "author": g(r"jdgm-rev__author'>(.*?)</span>"),
        "rating": int(score.group(1)) if score else 5,
        "title": g(r"jdgm-rev__title'>(.*?)</strong>"),
        "body": g(r"jdgm-rev__body'>(.*?)</div>"),
        "product": g(r"jdgm-rev__prod-link'>(.*?)</a>"),
        "date": date.group(1)[:10] if date else "",
    })
with open(os.path.join(OUT, "reviews.json"), "w", encoding="utf-8") as f:
    json.dump({"average": 4.44, "count": 119, "reviews": reviews}, f, ensure_ascii=False, indent=1)

# ---------- blog (Atom feed) ----------
atom = read("blog.atom")
article_images = {}
for f in sorted(os.listdir(SITE)):
    if f.startswith("blog_") and f.endswith(".html"):
        page = read(f)

        hrefs, imgs = [], []
        for h in re.findall(r'href="(/blogs/kami-blog/[^"#?]+)"', page):
            if h not in hrefs and "/tagged/" not in h:
                hrefs.append(h)
        for i in re.findall(r'src="//www\.kami-skincare\.com/cdn/shop/articles/([^"?& ]+)', page):
            if i not in imgs:
                imgs.append(i)
        if len(hrefs) == len(imgs):
            for h, i in zip(hrefs, imgs):
                article_images[h] = "https://cdn.shopify.com/s/files/1/0907/4042/5090/articles/" + i
        else:
            print("blog page mismatch", f, len(hrefs), len(imgs))
posts = []
for e in re.findall(r"<entry>(.*?)</entry>", atom, re.S):
    def tag(t):
        m = re.search(rf"<{t}[^>]*>(.*?)</{t}>", e, re.S)
        return html.unescape(m.group(1)) if m else ""
    content = tag("content")
    img = re.search(r'<img[^>]+src="([^"]+)"', content)
    link = re.search(r'<link[^>]+href="([^"]+)"', e)
    path = re.sub(r"^https://www\.kami-skincare\.com", "", link.group(1)) if link else ""
    posts.append({
        "title": html.unescape(tag("title")),
        "date": tag("published")[:10],
        "author": clean(tag("author")),
        "summary": (clean(tag("summary")) or clean(content))[:300],
        "image": article_images.get(path) or (("https:" + img.group(1)) if img and img.group(1).startswith("//") else (img.group(1) if img else "")),
        "url": link.group(1) if link else "",
        "html": content,
    })
with open(os.path.join(OUT, "blog.json"), "w", encoding="utf-8") as f:
    json.dump(posts, f, ensure_ascii=False, indent=1)

print(len(out_products), "products,", len(faq), "faq,", len(ingredients), "ingredients,",
      len(reviews), "reviews,", len(posts), "posts")
