"""Multi-channel broadcast engine.

Fans every alert out to public, discoverable social surfaces so the monitor
grows its own audience 24/7 with no manual labour. Each channel is gated on its
own environment secrets and fails soft — a missing token or a down API never
blocks the other channels or the monitor loop.

Channels (all optional, activate by setting the secrets):
  - Telegram        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  - Public Discord  DISCORD_WEBHOOK_PUBLIC
  - Bluesky         BLUESKY_HANDLE, BLUESKY_APP_PASSWORD
  - Mastodon        MASTODON_INSTANCE, MASTODON_TOKEN
  - X / Twitter     X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
                    (only high-value posts, to conserve the free-tier ~500/mo cap)

A `post` dict (built by monitor.build_broadcast_post) carries a pre-formatted
message per platform plus the shared fields:
  {
    "embed": <discord embed dict>,   # reused for the public Discord feed
    "image_url": str,
    "telegram_html": str,            # HTML-formatted
    "social_text": str,              # plain text (Mastodon)
    "x_text": str,                   # <=280, includes the buy URL
    "bluesky_text": str,             # <=300, headline only (URL rides the card)
    "buy_url": str,
    "money": str,                    # e.g. "£89.90"
    "store": str,
    "title": str,
    "priority": bool,                # gates the X channel
  }
"""

import os
import json
import time
import hmac
import base64
import hashlib
import secrets as _secrets
from urllib.parse import quote
from datetime import datetime, timezone

import httpx

TIMEOUT = 10.0


# ---------------------------------------------------------------------------
# Telegram  (Bot API — free, unlimited, image preview via sendPhoto)
# ---------------------------------------------------------------------------

def _telegram(post: dict) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return False
    api = f"https://api.telegram.org/bot{token}/"
    text = post["telegram_html"]
    image = post.get("image_url")
    if image:
        r = httpx.post(
            api + "sendPhoto",
            json={"chat_id": chat, "photo": image, "caption": text, "parse_mode": "HTML"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return True
        # Bad image URL etc. — fall back to a plain text message.
    r = httpx.post(
        api + "sendMessage",
        json={"chat_id": chat, "text": text, "parse_mode": "HTML",
              "disable_web_page_preview": False},
        timeout=TIMEOUT,
    )
    return r.status_code == 200


# ---------------------------------------------------------------------------
# Public Discord feed  (reuse the rich embed already built for the owner alert)
# ---------------------------------------------------------------------------

def _discord_public(post: dict) -> bool:
    url = os.environ.get("DISCORD_WEBHOOK_PUBLIC")
    embed = post.get("embed")
    if not (url and embed):
        return False
    r = httpx.post(url, json={"embeds": [embed]}, timeout=TIMEOUT)
    return r.status_code in (200, 204)


# ---------------------------------------------------------------------------
# Bluesky  (AT Protocol — free, open, no approval; link rides an external card)
# ---------------------------------------------------------------------------

def _bluesky(post: dict) -> bool:
    handle = os.environ.get("BLUESKY_HANDLE")
    pw = os.environ.get("BLUESKY_APP_PASSWORD")
    if not (handle and pw):
        return False
    base = "https://bsky.social/xrpc/"
    s = httpx.post(base + "com.atproto.server.createSession",
                   json={"identifier": handle, "password": pw}, timeout=TIMEOUT)
    if s.status_code != 200:
        print(f"  [WARN] bluesky auth {s.status_code}")
        return False
    sess = s.json()
    record = {
        "$type": "app.bsky.feed.post",
        "text": post["bluesky_text"][:300],
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "embed": {
            "$type": "app.bsky.embed.external",
            "external": {
                "uri": post["buy_url"],
                "title": post["title"][:280],
                "description": f"{post['money']} @ {post['store']}"[:300],
            },
        },
    }
    r = httpx.post(
        base + "com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {sess['accessJwt']}"},
        json={"repo": sess["did"], "collection": "app.bsky.feed.post", "record": record},
        timeout=TIMEOUT,
    )
    return r.status_code == 200


# ---------------------------------------------------------------------------
# Mastodon  (free, per-instance API token)
# ---------------------------------------------------------------------------

def _mastodon(post: dict) -> bool:
    instance = os.environ.get("MASTODON_INSTANCE")  # e.g. "mastodon.social"
    token = os.environ.get("MASTODON_TOKEN")
    if not (instance and token):
        return False
    instance = instance.replace("https://", "").rstrip("/")
    r = httpx.post(
        f"https://{instance}/api/v1/statuses",
        headers={"Authorization": f"Bearer {token}"},
        data={"status": post["social_text"]},
        timeout=TIMEOUT,
    )
    return r.status_code == 200


# ---------------------------------------------------------------------------
# X / Twitter  (OAuth 1.0a user context — high-value posts only)
# ---------------------------------------------------------------------------

def _oauth1_header(method: str, url: str, ck: str, cs: str, token: str, tsecret: str) -> str:
    def pe(s: str) -> str:
        return quote(str(s), safe="~")

    oauth = {
        "oauth_consumer_key": ck,
        "oauth_nonce": _secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": token,
        "oauth_version": "1.0",
    }
    param_str = "&".join(f"{pe(k)}={pe(v)}" for k, v in sorted(oauth.items()))
    base_str = "&".join([method.upper(), pe(url), pe(param_str)])
    signing_key = f"{pe(cs)}&{pe(tsecret)}"
    sig = base64.b64encode(
        hmac.new(signing_key.encode(), base_str.encode(), hashlib.sha1).digest()
    ).decode()
    oauth["oauth_signature"] = sig
    return "OAuth " + ", ".join(f'{pe(k)}="{pe(v)}"' for k, v in sorted(oauth.items()))


def _x(post: dict) -> bool:
    # Conserve the free-tier ~500 posts/month cap: only high-value events.
    if not post.get("priority"):
        return False
    ck = os.environ.get("X_API_KEY")
    cs = os.environ.get("X_API_SECRET")
    at = os.environ.get("X_ACCESS_TOKEN")
    ats = os.environ.get("X_ACCESS_SECRET")
    if not all([ck, cs, at, ats]):
        return False
    url = "https://api.twitter.com/2/tweets"
    body = json.dumps({"text": post["x_text"]})
    header = _oauth1_header("POST", url, ck, cs, at, ats)
    r = httpx.post(url, content=body,
                   headers={"Authorization": header, "Content-Type": "application/json"},
                   timeout=TIMEOUT)
    return r.status_code in (200, 201)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_CHANNELS = [
    ("telegram", _telegram),
    ("discord", _discord_public),
    ("bluesky", _bluesky),
    ("mastodon", _mastodon),
    ("x", _x),
]


def configured_channels() -> list[str]:
    """Names of channels that have their secrets set (for startup logging)."""
    checks = {
        "telegram": bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")),
        "discord": bool(os.environ.get("DISCORD_WEBHOOK_PUBLIC")),
        "bluesky": bool(os.environ.get("BLUESKY_HANDLE") and os.environ.get("BLUESKY_APP_PASSWORD")),
        "mastodon": bool(os.environ.get("MASTODON_INSTANCE") and os.environ.get("MASTODON_TOKEN")),
        "x": bool(os.environ.get("X_API_KEY") and os.environ.get("X_ACCESS_TOKEN")),
    }
    return [name for name, on in checks.items() if on]


def broadcast_all(post: dict) -> list[str]:
    """Send `post` to every configured channel. Returns the channels that fired.

    Fails soft per channel — one dead API never affects the others.
    """
    fired = []
    for name, fn in _CHANNELS:
        try:
            if fn(post):
                fired.append(name)
        except Exception as exc:
            print(f"  [WARN] broadcast {name}: {exc}")
    if fired:
        print(f"  broadcast -> {', '.join(fired)}")
    return fired
