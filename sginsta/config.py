"""Settings. Secrets come from environment variables (GitHub secrets)."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
DATA = ROOT / "data"
FONTS = ROOT / "assets" / "fonts"
LOGO = ROOT / "assets" / "logo.png"

TZ = ZoneInfo("Asia/Kolkata")
SITE = "https://aistudygroup.aipune.org"
NEXT_LINK = "aistudygroup.aipune.org/next"
HASHTAGS = "#AIStudyGroup #AIPune #Pune #BuildWithAI #LearnAI"

# Weekly queues: weekday (Mon=0) on which the next row of each CSV goes out.
TIP_DAY = 2          # Wednesday
SPOTLIGHT_DAY = 4    # Friday
QUEUE_TIME = "18:30"  # IST
REMINDER_TIME = "18:00"  # IST, the evening before a session

# Instagram card colours, taken from the site's home page.
PAPER, INK, TOMATO, SUN, SAGE = "#f4efe5", "#20211c", "#e95631", "#f6c84a", "#a5b99a"

IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
IG_API_VERSION = os.environ.get("IG_API_VERSION", "v24.0")
# Public base URL that serves this repo's files, used for image_url. In Actions this is
# raw.githubusercontent.com/<repo>/<commit>; see cli.media_base().
MEDIA_BASE = os.environ.get("MEDIA_BASE", "")
