# Replaces the Film section of media.md with my Letterboxd watchlist (scraped, Letterboxd has no public API).
import html, re, sys, urllib.request
from mal import replace

SITE = "https://letterboxd.com"
USER = "wyatt_g"

def get(path):
    req = urllib.request.Request(SITE + path, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req).read().decode()

def films():
    page = 1
    while True:
        items = re.findall(r'data-item-name="([^"]*)"[^>]*?data-item-link="([^"]*)"', get(f"/{USER}/watchlist/page/{page}/"))
        if not items:
            return
        yield from items
        page += 1

def line(name, link):
    m = re.fullmatch(r"(.*) \((\d{4})\)", html.unescape(name))
    title, year = m.groups() if m else (html.unescape(name), "")
    director = re.search(r'name="twitter:data1" content="([^"]*)"', get(link))
    return f"* **{title}**" + (f" — *{html.unescape(director[1])}*" if director else "") + (f" ({year})" if year else "")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "media.md"
    md = open(path).read()
    md = replace(md, "Film", [line(*f) for f in films()])
    open(path, "w").write(md)
