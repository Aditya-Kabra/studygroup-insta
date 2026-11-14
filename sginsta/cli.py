import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import config as C, instagram, posts


def cmd_plan(a):
    posts.sync_event()
    posts.sync_queues()


def cmd_publish(a):
    """Publish the earliest due post. One per run, so the feed never gets a burst."""
    due = [p for p in posts.all_posts() if p["status"] == "ready" and p["publish_at"] <= posts.now().isoformat()]
    if not due:
        print("Nothing due")
        return
    if not C.IG_ACCESS_TOKEN or not C.MEDIA_BASE:
        print(f"{len(due)} due, but IG_ACCESS_TOKEN or MEDIA_BASE is not set, so nothing was posted")
        return
    p = due[0]
    urls = [f"{C.MEDIA_BASE.rstrip('/')}/posts/{p['id']}/{img}" for img in p["images"]]
    try:
        p["ig_id"] = instagram.post(urls, p["caption"])
        p["status"], p["posted_at"] = "posted", posts.now().isoformat(timespec="minutes")
        print(f"Posted {p['id']} -> {p['ig_id']}")
    except Exception as e:
        p["status"], p["error"] = "failed", str(e)[:500]
        posts.save(p)
        raise
    posts.save(p)


def cmd_recap(a):
    src = Path(a.photos)
    photos = sorted(f for f in src.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic", ".webp"))[:10]
    if not photos:
        sys.exit(f"No photos in {src}")
    pid = a.id or f"recap-{posts.now():%Y-%m-%d}"
    d = posts.folder(pid)
    images = []
    for i, f in enumerate(photos, 1):
        posts.render.photo(f, d / f"{i}.jpg")
        images.append(f"{i}.jpg")
    when = datetime.fromisoformat(a.when).replace(tzinfo=C.TZ) if a.when else posts.now()
    caption = Path(a.caption_file).read_text() if a.caption_file else a.caption
    posts.new(pid, "recap", when, f"{caption}\n\n{C.HASHTAGS}", images, "draft" if a.draft else "ready")


def _set(pid, status):
    p = posts.load(pid)
    p["status"] = status
    posts.save(p)
    print(f"{pid}: {status}")


def cmd_list(a):
    for p in posts.all_posts():
        if a.all or p["status"] != "posted":
            print(f"{p['publish_at']}  {p['status']:7} {p['kind']:9} {p['id']}")


def cmd_refresh(a):
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(instagram.refresh_token(C.IG_ACCESS_TOKEN))
    print("Refreshed Instagram token")


def cmd_whoami(a):
    print(instagram.account())


def main():
    ap = argparse.ArgumentParser(prog="sginsta")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("plan", help="queue the next session's posts and this week's tip or spotlight")
    sp.add_parser("publish", help="post the earliest due post to Instagram")
    r = sp.add_parser("recap", help="queue a carousel of meetup photos")
    r.add_argument("photos")
    r.add_argument("--caption", default="")
    r.add_argument("--caption-file")
    r.add_argument("--when", help="YYYY-MM-DD HH:MM in IST; default now")
    r.add_argument("--id")
    r.add_argument("--draft", action="store_true", help="hold until approved")
    for name, status in (("approve", "ready"), ("hold", "draft")):
        s = sp.add_parser(name)
        s.add_argument("id")
        s.set_defaults(status=status)
    l = sp.add_parser("list")
    l.add_argument("--all", action="store_true")
    f = sp.add_parser("refresh-token")
    f.add_argument("--out", required=True)
    sp.add_parser("whoami", help="check the token: print the Instagram account")
    a = ap.parse_args()
    if a.cmd in ("approve", "hold"):
        return _set(a.id, a.status)
    {"plan": cmd_plan, "publish": cmd_publish, "recap": cmd_recap, "list": cmd_list,
     "refresh-token": cmd_refresh, "whoami": cmd_whoami}[a.cmd](a)
