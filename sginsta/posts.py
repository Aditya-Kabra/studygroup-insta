"""The post queue. Each post is a folder in posts/: post.json plus its JPEGs.

status: draft (held until approved) -> ready (goes out at publish_at) -> posted (or failed).
"""
import csv
import html
import json
import re
from datetime import date, datetime, timedelta

import requests

from . import config as C, render


def now():
    return datetime.now(C.TZ)


def at(day, hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime(day.year, day.month, day.day, h, m, tzinfo=C.TZ)


def load(pid):
    return json.loads((C.POSTS / pid / "post.json").read_text())


def save(p):
    (C.POSTS / p["id"] / "post.json").write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n")


def all_posts():
    return sorted((load(d.name) for d in C.POSTS.iterdir() if (d / "post.json").exists()),
                  key=lambda p: p["publish_at"])


def exists(pid):
    return (C.POSTS / pid / "post.json").exists()


def new(pid, kind, publish_at, caption, images, status="ready"):
    p = dict(id=pid, kind=kind, publish_at=publish_at.isoformat(timespec="minutes"),
             caption=caption.strip(), images=images, status=status, ig_id=None, posted_at=None)
    save(p)
    print(f"Queued {pid} ({status}) for {p['publish_at']}")
    return p


def folder(pid):
    d = C.POSTS / pid
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- next session, from the live site

def _og(page, prop):
    m = re.search(rf'property="og:{prop}" content="([^"]*)"', page) or \
        re.search(rf'og:{prop}" content="([^"]*)"', page)
    return html.unescape(m.group(1)) if m else ""


def next_event():
    """The session /next points at: slug, day, title, blurb. None if there isn't one."""
    r = requests.get(f"{C.SITE}/next", allow_redirects=False, timeout=30)
    loc = r.headers.get("location", "")
    m = re.search(r"/events/((\d{4}-\d{2}-\d{2})-[\w-]+)", loc)
    if not m:
        return None
    page = requests.get(C.SITE + "/events/" + m.group(1), timeout=30).text
    title = _og(page, "title").split(" | ")[0]
    return dict(slug=m.group(1), day=date.fromisoformat(m.group(2)), title=title,
                blurb=_og(page, "description"), url=f"{C.SITE}/events/{m.group(1)}")


def sync_event():
    """Queue an announcement and a reminder for the next session, once each."""
    e = next_event()
    if not e or e["day"] < now().date():
        print("No upcoming session on the site")
        return
    top = e["day"].strftime("%a %-d %b")
    pid = f"{e['slug']}-announce"
    if not exists(pid):
        render.card(folder(pid) / "1.jpg", kicker="AI Study Group · Pune", top=top,
                    headline=e["title"], body=e["blurb"], footer="Free sign-up, link in bio")
        # Goes out at the next run, so there is one run's gap to look at it and hold it if needed.
        new(pid, "event", now() + timedelta(hours=2), f"""{e['title']} 🛠️

{e['blurb']}

Bring a laptop and something you want to try. Sign up: {C.NEXT_LINK} (link in bio)

{C.HASHTAGS}""", ["1.jpg"])
    pid = f"{e['slug']}-reminder"
    when = at(e["day"] - timedelta(days=1), C.REMINDER_TIME)
    if not exists(pid) and when > now():
        render.card(folder(pid) / "1.jpg", kicker="AI Study Group · Pune", top="Tomorrow",
                    headline=e["title"], body=e["blurb"], footer="Still time to sign up")
        new(pid, "event", when, f"""Tomorrow: {e['title']}

{e['blurb']}

Last call to grab a spot: {C.NEXT_LINK} (link in bio)

{C.HASHTAGS}""", ["1.jpg"])


# ---------------------------------------------------------------- weekly queues from CSV

def _rows(name):
    path = C.DATA / name
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if r.get("id") and not (r.get("status") or "").strip()]


def sync_queues(today=None):
    """On tip day and spotlight day, queue the next unused row (rows with any status are skipped)."""
    today = today or now().date()
    if today.weekday() == C.TIP_DAY:
        _queue_one("tips.csv", "tip", today, _tip)
    if today.weekday() == C.SPOTLIGHT_DAY:
        _queue_one("projects.csv", "spotlight", today, _spotlight)


def _queue_one(csv_name, kind, today, make):
    if any(p["kind"] == kind and p["publish_at"][:10] == today.isoformat() for p in all_posts()):
        return
    for r in _rows(csv_name):
        pid = f"{kind}-{r['id']}"
        if not exists(pid):
            caption = make(r, folder(pid) / "1.jpg")
            new(pid, kind, at(today, C.QUEUE_TIME), caption, ["1.jpg"])
            return
    print(f"{csv_name}: nothing left to post")


def _tip(r, out):
    render.card(out, kicker="AI Study Group · Tip", top=f"Tip {r['id']}", headline=r["title"],
                body=r["body"], footer="Try it at the next session")
    return f"{r['title']}\n\n{r['body']}\n\nCome try it with us: {C.NEXT_LINK}\n\n{C.HASHTAGS}"


def _spotlight(r, out):
    render.card(out, kicker="Built at AI Study Group", top=f"by {r['maker']}", headline=r["project"],
                body=r["what"], bg=C.SAGE, footer="Built in one session")
    handle = f" ({r['handle']})" if r.get("handle") else ""
    link = f"\n\n{r['link']}" if r.get("link") else ""
    return (f"{r['project']}, built by {r['maker']}{handle} at AI Study Group.\n\n{r['what']}{link}"
            f"\n\nWant to build yours? {C.NEXT_LINK}\n\n{C.HASHTAGS}")
