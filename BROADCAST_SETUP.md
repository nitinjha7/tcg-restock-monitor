# Broadcast Setup — Activating Public Channels

The monitor auto-posts every live restock/preorder/price-drop to any channel
whose secrets are set. Add the secrets under **GitHub → Settings → Secrets and
variables → Actions → New repository secret**. Set only the channels you want —
unset channels are silently skipped. No code changes needed.

Fastest to slowest to set up: **Telegram → Discord → Bluesky → Mastodon → X**.

---

## 1. Telegram  *(free, unlimited, ~2 min — do this first)*

1. In Telegram, message **@BotFather** → `/newbot` → follow prompts → copy the
   **bot token**.
2. Create a **public channel** (e.g. `@tcgrestocksuk`). Add your bot as an
   **admin** (Post Messages permission).
3. Get the chat ID: post any message in the channel, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and read
   `chat.id` — or just use the public `@handle` as the chat ID.

| Secret | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | the BotFather token |
| `TELEGRAM_CHAT_ID` | `@yourchannel` (or the numeric id) |

---

## 2. Public Discord feed  *(free, ~1 min)*

1. Make a public server (or a channel in one) + a permanent invite link.
2. Channel → **Edit → Integrations → Webhooks → New Webhook → Copy URL**.

| Secret | Value |
|---|---|
| `DISCORD_WEBHOOK_PUBLIC` | the webhook URL |

Alerts here are **live** (not the 24h-delayed free tier) — that's intentional
for growth. Share the invite everywhere.

---

## 3. Bluesky  *(free, open API, ~3 min)*

1. Create an account (e.g. `tcgrestocks.bsky.social`).
2. **Settings → App Passwords → Add App Password** → copy it (this is NOT your
   main password).

| Secret | Value |
|---|---|
| `BLUESKY_HANDLE` | `tcgrestocks.bsky.social` |
| `BLUESKY_APP_PASSWORD` | the app password |

---

## 4. Mastodon  *(free, ~3 min)*

1. Pick an instance (e.g. `mastodon.social`) and register.
2. **Preferences → Development → New application** → scopes: `write:statuses` →
   create → copy **Your access token**.

| Secret | Value |
|---|---|
| `MASTODON_INSTANCE` | `mastodon.social` |
| `MASTODON_TOKEN` | the access token |

---

## 5. X / Twitter  *(free tier ~500 posts/month — high-value posts only)*

Only restocks/preorders **≥ £30** (booster-box territory) are posted to X, to
stay under the free cap. Set `X_MIN_PRICE` in `monitor.py` to tune.

1. Create an account, then apply at **developer.x.com** (Free tier).
2. Create a Project + App. Set app permissions to **Read and Write**.
3. Generate **API Key & Secret** (consumer keys) and **Access Token & Secret**
   (for your account). Regenerate the access token *after* setting Read+Write.

| Secret | Value |
|---|---|
| `X_API_KEY` | API Key (consumer key) |
| `X_API_SECRET` | API Secret |
| `X_ACCESS_TOKEN` | Access Token |
| `X_ACCESS_SECRET` | Access Token Secret |

---

## Verifying

After adding secrets, re-dispatch the workflow (Actions → tcg-monitor → Run
workflow). The log's first lines print:

```
Broadcast channels active: telegram, discord, bluesky
```

Channels only *post* when a real event fires. To test immediately without
waiting for a natural restock, temporarily edit `state.json` (flip a product's
`available` to `false`), let one cycle run, and it'll fire a RESTOCK to every
active channel.
