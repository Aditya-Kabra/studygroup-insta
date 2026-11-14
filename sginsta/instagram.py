"""Instagram posting through the official Instagram API with Instagram Login.

Adapted from dadabase-daily. Instagram fetches each image from a public URL, and only JPEG works.
"""
import time

import requests

from . import config

BASE = "https://graph.instagram.com"


def _h():
    return {"Authorization": f"Bearer {config.IG_ACCESS_TOKEN}"}


def _url(path):
    return f"{BASE}/{config.IG_API_VERSION}/{path.lstrip('/')}"


def _check(r):
    try:
        data = r.json()
    except ValueError:
        r.raise_for_status()
        raise
    if r.status_code >= 400 or "error" in data:
        raise RuntimeError(f"Instagram API error {r.status_code}: {data.get('error', data)}")
    return data


def account():
    d = _check(requests.get(_url("me"), params={"fields": "user_id,username"}, headers=_h(), timeout=30))
    return {"id": d.get("user_id") or d["id"], "username": d.get("username", "")}


def _wait_ready(cid, timeout_s=600):
    start = time.time()
    while time.time() - start < timeout_s:
        d = _check(requests.get(_url(cid), params={"fields": "status_code,status"}, headers=_h(), timeout=30))
        if d.get("status_code") == "FINISHED":
            return
        if d.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram could not process media {cid}: {d}")
        time.sleep(5)
    raise TimeoutError(f"Instagram media {cid} still processing after {timeout_s}s")


def _create(ig, **fields):
    return _check(requests.post(_url(f"{ig}/media"), data=fields, headers=_h(), timeout=60))["id"]


def post(image_urls, caption):
    """One image becomes a single post; 2 to 10 become a carousel. Returns the media id."""
    ig = account()["id"]
    if len(image_urls) == 1:
        cid = _create(ig, image_url=image_urls[0], caption=caption)
    else:
        kids = [_create(ig, image_url=u, is_carousel_item="true") for u in image_urls[:10]]
        for k in kids:
            _wait_ready(k)
        cid = _create(ig, media_type="CAROUSEL", children=",".join(kids), caption=caption)
    _wait_ready(cid)
    return _check(requests.post(_url(f"{ig}/media_publish"), data={"creation_id": cid}, headers=_h(), timeout=60))["id"]


def refresh_token(token):
    """Swap a long-lived token for a fresh 60-day one."""
    d = _check(requests.get(f"{BASE}/refresh_access_token",
                            params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30))
    return d["access_token"]
