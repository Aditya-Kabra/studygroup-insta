# AI Study Group on Instagram

Posts to the study group's Instagram on its own. Modelled on
[dadabase-daily](https://github.com/AdG1382/dadabase-daily).

## What goes out

| Post | Where it comes from | When |
|---|---|---|
| Session announcement | The session `/next` points to on aistudygroup.aipune.org (title and blurb) | The run after it appears on the site |
| Session reminder | Same | 18:00 IST the evening before |
| Weekly tip | Next row of `data/tips.csv` | Wednesdays 18:30 IST |
| Project spotlight | Next row of `data/projects.csv` | Fridays 18:30 IST |
| Meetup recap | Photos you hand it (`recap` command) | When you say |

A GitHub Action runs at 09:00, 12:00, 15:00, 18:00 and 21:00 IST. Each run queues new posts,
then publishes at most one post that is due. Mondays it renews the Instagram token.

## The queue

Every post is a folder in `posts/`: `post.json` plus its images. Open the folder on GitHub to
see exactly what will go out. `status` is:

- `draft`: held. Nothing happens until you approve it.
- `ready`: goes out at `publish_at`.
- `posted` / `failed`: done; `failed` keeps the error.

Announcements wait one run after being queued, so you have about three hours to hold one.
To hold or release a post, edit `status` on GitHub, or locally:

```bash
python -m sginsta list
python -m sginsta hold 2026-11-22-build-and-share-announce
python -m sginsta approve recap-2026-11-16
```

CSV rows post only when their `status` is empty. Type `draft` to keep a row back, `cut` to drop it.

## Meetup recap

```bash
python -m sginsta recap ~/Desktop/meetup-photos --caption "Twenty people, nine voice agents..." --when "2026-11-16 19:00"
```

Takes up to 10 photos (JPEG, PNG or HEIC), crops them to 4:5, and queues a carousel. Add `--draft`
to look first. Commit and push `posts/`; the next run after `--when` posts it.

## Setup

1. Instagram app → switch the group's account to **Professional** (Creator or Business).
2. Meta app (developers.facebook.com) → Use cases → *Manage messaging & content on Instagram* →
   **API setup with Instagram login** → add the account, then **Generate token** with
   `instagram_business_basic` and `instagram_business_content_publish`.
3. While the app is in development mode, the account must be added as an *Instagram Tester* under
   App roles and accept the invite (Instagram → Settings → Website permissions → Tester invites).
4. Repo → Settings → Secrets and variables → Actions:
   - `IG_ACCESS_TOKEN`: the token from step 2.
   - `GH_PAT`: fine-grained token, this repo only, *Secrets: read and write* (for the token refresh).
5. Check the token: `IG_ACCESS_TOKEN=... python -m sginsta whoami`.

The repo must be **public**: Instagram downloads each image from raw.githubusercontent.com.
No secrets live in the code.

Fonts: Inter and Instrument Serif, both SIL Open Font License (see `assets/fonts`).
