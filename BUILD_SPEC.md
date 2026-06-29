# TCG Sealed-Product Restock Monitor — Build Spec for Claude Code

You are building a 24/7 monitor that watches independent TCG card shops (running on Shopify)
for sealed-product restocks, new preorders, and price drops, and fires Discord alerts.

It must run FREE on GitHub Actions (no server, no credit card). State persists between runs
by committing a small JSON file back to the repo.

------------------------------------------------------------
## 1. WHAT IT DOES (plain English)

Every run (GitHub Actions, every ~5 minutes):
1. Fetch each store's public `https://{store}/products.json?limit=250&page=N` (no auth needed).
2. Keep ONLY sealed products (booster boxes, ETBs, cases, tins, bundles). Discard singles,
   graded cards, accessories, Funko, Warhammer minis, event tickets, $0.00 junk.
3. Compare each kept product against last-seen state (stored in state.json).
4. Detect three event types:
   - RESTOCK: product went from available=false -> available=true
   - NEW PREORDER: a sealed product we've never seen before, that is available and tagged preorder
   - PRICE DROP: price decreased by >= 5% vs last seen
5. For each event, send a Discord alert to the LIVE webhook immediately, and queue the same
   alert (in state.json) for release to the FREE webhook 24 hours later.
6. On every run, also release any queued alerts whose 24h delay has elapsed to the FREE webhook.
7. Save updated state.json and commit it back to the repo.

------------------------------------------------------------
## 2. STORES TO MONITOR (confirmed working)

Put these in a config file `stores.json`. All confirmed to serve public /products.json.

```json
[
  {"name": "Total Cards",        "domain": "totalcards.net"},
  {"name": "Otakura",            "domain": "otakura.com"},
  {"name": "Ripperholics",       "domain": "ripperholics.com"},
  {"name": "Undiscovered Realm", "domain": "undiscoveredrealm.com"},
  {"name": "Pack Fresh",         "domain": "pack-fresh.com"},
  {"name": "Skybox CT",          "domain": "skyboxct.com"},
  {"name": "Flipside Gaming",    "domain": "flipsidegaming.com"},
  {"name": "Stomping Grounds",   "domain": "stompinggroundstcg.com"},
  {"name": "Common Lands",       "domain": "commonlands... (use the pack-fresh-linked domain)"}
]
```
(Use the 8 clean domains you have; add more later. Domain list is data, not code — easy to extend.)

------------------------------------------------------------
## 3. THE FILTER (most important part — derived from real store data)

A product is KEPT only if it passes ALL of these:

### 3a. product_type / title must look like SEALED product
Keep if the lowercased `product_type` OR `title` contains ANY of:
  "booster box", "booster case", "booster display", "hobby box", "hobby case",
  "elite trainer box", "etb", "booster bundle", "bundle", "blister",
  "mini tin", " tin", "booster pack", "build & battle", "build and battle",
  "starter deck", "case (", "12-box", "20-box", "6-box", "display"
  (Italian/EU equivalents seen in data: "booster box da", "set allenatore", "bustina", "blister")

### 3b. HARD EXCLUDES (if any match, discard immediately, even if 3a matched)
Discard if lowercased `product_type` is any of:
  "single", "single card", "single raw card", "graded tcg/ccg", "graded", "pop vinyl",
  "model kit", "miniatures", "figurines", "playmat", "deck box", "sleeves"
Discard if lowercased `title` contains any of:
  "psa ", "cgc ", "ace ", "slab", " foil", "art rare", "/165", "/193", "/217", "/078",
  "funko", "pop!", "nendoroid", "warhammer", "games workshop", "astra militarum",
  "battleforce", "dragon shield", "ultra pro", "deck box", "playmat", "sleeve",
  "event entry", "draft entry", "event reservation", "tournament"
Discard if `vendor` is any of:
  "Games Workshop", "Funko", "Good Smile Company", "Ultimate Guard", "Dragon Shield",
  "Ultra PRO"

### 3c. PRICE sanity
Discard the product if its first variant price == "0.00" (these are placeholder/out-of-stock junk).
Discard if price < 15 (sealed boxes are never under ~$15; filters stray packs/promos if you want
boxes only — make this a config threshold MIN_PRICE so it's tunable).

### 3d. OPTIONAL game focus (config flag)
Add a config list `WATCH_GAMES = ["one piece","lorcana","pokemon","pokémon","riftbound","gundam","yu-gi-oh","yugioh","union arena"]`.
If set, keep only products whose title/body/tags mention one of these. Leave broad at first;
narrow later if the feed is noisy.

------------------------------------------------------------
## 4. STATE MODEL (state.json, committed back to repo)

```json
{
  "products": {
    "{store_domain}::{product_id}::{variant_id}": {
      "available": true,
      "price": 78.00,
      "title": "Yu-Gi-Oh! Chaos Origins Booster Box",
      "last_seen": "2026-06-29T10:00:00Z"
    }
  },
  "delayed_queue": [
    {"release_at": "2026-06-30T10:00:00Z", "payload": { ...same fields as a live alert... }}
  ],
  "known_product_ids": ["totalcards.net::123", "..."]
}
```

Key = domain + product_id + variant_id (so multi-variant boxes are tracked per variant).
`known_product_ids` is used to detect NEW preorders (product_id never seen before).

------------------------------------------------------------
## 5. EVENT DETECTION LOGIC

For each kept variant this run, compare to state.products[key]:
- If key not in state AND product_id not in known_product_ids:
    -> if available and (tagged preorder/preordine OR title contains "pre-order"/"preorder"):
         emit NEW_PREORDER event.
    -> (if available but not a preorder, just record it silently — it's pre-existing stock,
        not a fresh signal. Only alert NEW preorders, not first-time-seen in-stock items,
        to avoid a flood on first run.)
- If key in state:
    - was available=false, now true  -> emit RESTOCK event
    - price dropped >= 5%             -> emit PRICE_DROP event (include old and new price)
Always update state.products[key] with current values and last_seen.
Add product_id to known_product_ids.

IMPORTANT — first-run guard: on the very first run state is empty. Do NOT alert on everything.
On first run, just populate state and send a single "monitor online, tracking N sealed products
across M stores" message to the LIVE webhook. Alerts begin from run 2.

------------------------------------------------------------
## 6. DISCORD ALERT FORMAT

Send via webhook POST (JSON). Use an embed. Example payload builder:

```
title:  "🟢 RESTOCK: {title}"  | "🆕 PREORDER: {title}" | "💸 PRICE DROP: {title}"
url:    "https://{store}/products/{handle}"     (direct buy link)
fields: Store={name}, Price=${price} (Was ${old} for drops), Status=In stock/Preorder
thumbnail: first product image src
footer: timestamp
color:  green restock / blue preorder / orange price drop
```

Two webhooks, both stored as GitHub Actions secrets:
- DISCORD_WEBHOOK_LIVE   (paid #live-alerts channel)
- DISCORD_WEBHOOK_FREE   (public #free-feed channel, gets 24h-delayed copies)

------------------------------------------------------------
## 7. TECH / FILES

- Python 3.11, stdlib + `httpx` only (no heavy deps).
- Files:
    monitor.py        (main script: fetch, filter, diff, alert, save)
    stores.json       (store list)
    state.json        (committed state; starts as {"products":{},"delayed_queue":[],"known_product_ids":[]})
    requirements.txt  (httpx)
    .github/workflows/monitor.yml  (schedule)
- Fetch politely: 1 request per store per page, 1–2s gap between stores, User-Agent header
  "Mozilla/5.0 (compatible; TCGMonitor/1.0)". Paginate until a page returns <250 products
  or page 3 (cap pages at 3 to stay fast on free runners).
- Wrap each store fetch in try/except: one store failing must not stop the others.

### .github/workflows/monitor.yml
```yaml
name: tcg-monitor
on:
  schedule:
    - cron: "*/5 * * * *"   # every 5 minutes (GitHub's practical minimum)
  workflow_dispatch:
permissions:
  contents: write           # needed to commit state.json back
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: python monitor.py
        env:
          DISCORD_WEBHOOK_LIVE: ${{ secrets.DISCORD_WEBHOOK_LIVE }}
          DISCORD_WEBHOOK_FREE: ${{ secrets.DISCORD_WEBHOOK_FREE }}
      - name: commit state
        run: |
          git config user.name "tcg-monitor"
          git config user.email "bot@local"
          git add state.json
          git diff --quiet --cached || git commit -m "update state [skip ci]"
          git push
```

------------------------------------------------------------
## 8. ACCEPTANCE TEST (must pass before going live)

Run locally once with a TEST webhook:
1. First run: prints "tracking N sealed products across M stores", N should be > 0 and should
   NOT include any single/graded/sleeve/funko/warhammer/event item. Spot-check 20 kept titles —
   all must be sealed boxes/ETBs/cases/tins.
2. Manually edit state.json: flip one known box's available to false, drop one box's price 20%.
   Re-run. It must emit exactly one RESTOCK and one PRICE_DROP, with correct buy links.
3. Confirm a delayed copy lands in delayed_queue with release_at = now+24h.
4. Wait/realign clock or temporarily set delay to 1 min: confirm queued item posts to FREE webhook.

If all four pass, deploy to GitHub Actions with the real LIVE and FREE webhooks.
