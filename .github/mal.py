# Replaces the Anime and Manga sections of media.md with my MAL plan-to-watch/read lists.
import json, os, re, sys, urllib.request

USER = "raiinyzen"
API = "https://api.myanimelist.net/v2/users/" + USER
ONGOING = {"currently_airing", "currently_publishing", "on_hiatus"}

def fetch(path):
    # ponytail: limit=1000 is MAL's max page size, follow paging.next if a list ever gets bigger
    req = urllib.request.Request(API + path, headers={"X-MAL-CLIENT-ID": os.environ["MAL_CLIENT_ID"]})
    return [d["node"] for d in json.load(urllib.request.urlopen(req))["data"]]

def years(n):
    start, end = n.get("start_date", "")[:4], n.get("end_date", "")[:4]
    if n.get("status") in ONGOING:
        return f" ({start}–)" if start else ""
    if start and end and start != end:
        return f" ({start}–{end})"
    return f" ({start})" if start else ""

def line(title, by, n):
    return f"* **{title}**" + (f" — *{by}*" if by else "") + years(n)

def anime():
    return [line(n["title"], " / ".join(s["name"] for s in n.get("studios", [])), n)
            for n in fetch("/animelist?status=plan_to_watch&limit=1000&fields=studios,start_date,end_date,status")]

def manga():
    def author(a):
        return " ".join(filter(None, [a["node"].get("first_name"), a["node"].get("last_name")]))
    return [line(n["title"], " & ".join(author(a) for a in n.get("authors", [])), n)
            for n in fetch("/mangalist?status=plan_to_read&limit=1000"
                           "&fields=authors{first_name,last_name},start_date,end_date,status")]

def replace(md, heading, lines):
    # section runs until the next top-level heading
    return re.sub(rf"(?ms)^# {heading}\n.*?(?=^# |\Z)", f"# {heading}\n\n" + "\n".join(lines) + "\n\n", md)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "media.md"
    md = open(path).read()
    md = replace(replace(md, "Anime", anime()), "Manga / LN", manga())
    open(path, "w").write(md)
