# Fills the generated sections of media.md: Anime and Manga / LN from MyAnimeList, Film from Letterboxd.
# A source that fails leaves its section as committed (empty) and the others still update.
import html, json, os, re, sys, traceback, urllib.request

MAL = "https://api.myanimelist.net/v2/users/raiinyzen"
LETTERBOXD = "https://letterboxd.com"
ONGOING = {"currently_airing", "currently_publishing", "on_hiatus"}

def get(url, **headers):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers)).read().decode()

def line(title, by, years):
    return f"* **{title}**" + (f" — *{by}*" if by else "") + (f" ({years})" if years else "")

def mal(path):
    # ponytail: limit=1000 is MAL's max page size, follow paging.next if a list ever gets bigger
    data = json.loads(get(MAL + path + ",alternative_titles&limit=1000", **{"X-MAL-CLIENT-ID": os.environ["MAL_CLIENT_ID"]}))["data"]
    for n in (d["node"] for d in data):
        start, end = n.get("start_date", "")[:4], n.get("end_date", "")[:4]
        if n.get("status") in ONGOING:
            years = f"{start}–" if start else ""
        else:
            years = f"{start}–{end}" if start and end and start != end else start
        # English title where MAL has one, romaji otherwise
        yield n, n.get("alternative_titles", {}).get("en") or n["title"], years

def anime():
    return [line(title, " / ".join(s["name"] for s in n.get("studios", [])), years)
            for n, title, years in mal("/animelist?status=plan_to_watch&fields=studios,start_date,end_date,status")]

def manga():
    def author(a):
        return " ".join(filter(None, [a["node"].get("first_name"), a["node"].get("last_name")]))
    return [line(title, " & ".join(author(a) for a in n.get("authors", [])), years)
            for n, title, years in mal("/mangalist?status=plan_to_read&fields=authors{first_name,last_name},start_date,end_date,status")]

def film():
    # Letterboxd has no public API, so scrape the watchlist pages and each film page for its director
    def page(path):
        return get(LETTERBOXD + path, **{"User-Agent": "Mozilla/5.0"})
    lines, n = [], 1
    while items := re.findall(r'data-item-name="([^"]*)"[^>]*?data-item-link="([^"]*)"', page(f"/wyatt_g/watchlist/page/{n}/")):
        for name, link in items:
            title, year = re.fullmatch(r"(.*?)(?: \((\d{4})\))?", html.unescape(name)).groups()
            director = re.search(r'name="twitter:data1" content="([^"]*)"', page(link))
            lines.append(line(title, director and html.unescape(director[1]), year))
        n += 1
    return lines

SECTIONS = {"Film": film, "Anime": anime, "Manga / LN": manga}

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "media.md"
    md, failed = open(path).read(), False
    for heading, source in SECTIONS.items():
        try:
            # section runs until the next top-level heading
            md = re.sub(rf"(?ms)^# {heading}\n.*?(?=^# |\Z)", lambda _: f"# {heading}\n\n" + "\n".join(source()) + "\n\n", md)
        except Exception:
            traceback.print_exc()
            failed = True
    open(path, "w").write(md)
    sys.exit(failed)
