# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A 24/7 TCG sealed-product restock monitor that polls Shopify stores and fires Discord alerts. Runs free on GitHub Actions. State persists between runs via `state.json` committed back to the repo.

Full specification is in `BUILD_SPEC.md`; growth/monetization strategy is in `STRATEGY.md`. Read `BUILD_SPEC.md` before changing core logic.

## Tech Stack

- **Python 3.11**, stdlib + `httpx` only (no other deps)
- **GitHub Actions** as a free always-on host (see Run Modes below)
- **Discord webhooks** for alerts (two tiers: live and 24h-delayed free)

## Run Modes

`monitor.py` has two modes:
- **Single run** (`python monitor.py`) — one fetch/diff/alert cycle, commits state, exits. Used for local testing and manual runs.
- **Loop** (`python monitor.py --loop`) — polls every ~60s continuously for ~5h50m, committing state every 20 min, then exits so the workflow re-dispatches a fresh job. This is the production mode: it gives near-real-time polling **for free** by exploiting unlimited Actions minutes on a **public** repo (private repos only get 2,000 min/month — the repo MUST be public for this).

The workflow (`.github/workflows/monitor.yml`) self-perpetuates: each job runs the loop, then re-dispatches itself via `gh workflow run`. A 6h `schedule` cron + a `concurrency` group are the safety net (restart if the chain breaks; never run two at once). `commit_state()` is a no-op outside Actions (gated on `$GITHUB_ACTIONS`).

## Planned File Structure

```
monitor.py                        # main script: fetch → filter → diff → alert → save
stores.json                       # store list (data, not code — easy to extend)
state.json                        # committed state between runs
requirements.txt                  # httpx only
.github/workflows/monitor.yml     # schedule + commit step
```

## Running & Testing

Always use a virtual environment for local work — do not install into the global interpreter.

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # POSIX

# Run locally (use a test Discord webhook)
DISCORD_WEBHOOK_LIVE=https://... DISCORD_WEBHOOK_FREE=https://... ./.venv/Scripts/python.exe monitor.py
```

For local end-to-end testing without real Discord webhooks, run a tiny HTTP server that
returns 204 and point both webhook env vars at it (see acceptance test below). On Windows the
console codepage mangles emoji/accents on print — set `PYTHONIOENCODING=utf-8` when inspecting
output; the JSON state itself is always valid UTF-8.

Acceptance test (from `BUILD_SPEC.md` §8):
1. First run → no alerts, prints "tracking N sealed products across M stores"
2. Manually flip `state.json` (set `available: false`, drop a price 20%) → re-run → exactly one RESTOCK + one PRICE_DROP
3. Confirm `delayed_queue` entry has `release_at = now+24h`
4. Lower delay or wait → confirm FREE webhook receives queued alert

## Architecture

### State Model (`state.json`)

```json
{
  "products": {
    "{domain}::{product_id}::{variant_id}": {
      "available": bool, "price": float, "title": str, "last_seen": "ISO8601"
    }
  },
  "delayed_queue": [{"release_at": "ISO8601", "payload": {...}}],
  "known_product_ids": ["domain::id", "..."]
}
```

State key = `domain + product_id + variant_id` (tracks multi-variant products per variant).

### Event Detection Logic

Compare each kept variant against `state.products[key]`:
- **Key not in state AND product_id not in `known_product_ids`** → if `available` and tagged preorder → emit `NEW_PREORDER` (otherwise record silently — no alert for first-seen in-stock items to avoid flood on first run)
- **Key in state, was `available=false`, now `true`** → emit `RESTOCK`
- **Key in state, price dropped ≥ 5%** → emit `PRICE_DROP`

**First-run guard**: when `state.products` is empty, populate state only — send one "monitor online" message, no product alerts.

### Two-Tier Webhook Delivery

- `DISCORD_WEBHOOK_LIVE` (env/secret): gets alerts immediately
- `DISCORD_WEBHOOK_FREE` (env/secret): gets same alerts 24 hours later via `delayed_queue`

On every run: fire immediate alerts → enqueue 24h-delayed copies → release any queued items whose `release_at` has elapsed.

### Store Fetching

- Endpoint: `https://{domain}/products.json?limit=250&page=N`
- Paginate until page returns < 250 products or page 3 (cap at 3 pages)
- `User-Agent: Mozilla/5.0 (compatible; TCGMonitor/1.0)`, 1–2s gap between stores
- Each store wrapped in `try/except` — one failure must not stop others
- **Null-field caveat:** Shopify feeds can return explicit `null` for fields like `body_html`,
  so `dict.get(key, "")` returns `None` (not `""`). Use the `_field()` helper in `monitor.py`
  for any product field that gets `.lower()`-ed.
- **Collection targeting:** A store config may include `"collections": ["handle", ...]`. When
  present, `fetch_store` pulls `/collections/{handle}/products.json` (deduped by product id)
  instead of the root feed. This is how big general retailers (Total Cards, 401 Games, Infinity
  Collectables) expose sealed stock — their root feed sorts singles/board-games first, pushing
  TCG sealed past the 3-page cap and yielding ~0. A non-existent collection handle returns HTTP
  200 with an empty `products` array (not a 404), so verify handles by checking the count is > 0.

### Product Filter (must pass ALL)

**Keep** if lowercased `product_type` or `title` contains any sealed-product keyword (booster box, ETB, tin, bundle, display, starter deck, etc. — full list in `BUILD_SPEC.md` §3a).

**Discard immediately** if:
- `product_type` is a hard-exclude (single, graded, pop vinyl, playmat, sleeves, etc.)
- `title` contains hard-exclude strings (PSA, CGC, slab, Funko, Warhammer, event entry, etc.)
- `vendor` is a hard-exclude (Games Workshop, Funko, Ultra PRO, etc.)
- First variant price is `"0.00"` or price < `MIN_PRICE` (default 15, configurable)

**Optional game focus**: `WATCH_GAMES` config list filters by game name in title/body/tags.

## Configuration

- `stores.json` — store list (domain + display name)
- `MIN_PRICE` — minimum price threshold (default 15), tunable config constant
- `WATCH_GAMES` — list of game names to focus on (leave broad initially)
- Secrets `DISCORD_WEBHOOK_LIVE` and `DISCORD_WEBHOOK_FREE` set in GitHub Actions repo settings

## Discord Alert Format

Embed with:
- Title: `🟢 RESTOCK: {title}` / `🆕 PREORDER: {title}` / `💸 PRICE DROP: {title}`
- URL: `https://{store}/products/{handle}` (direct buy link)
- Fields: Store, Price (Was/Now for drops), Status
- Thumbnail: first product image
- Color: green/blue/orange per event type
