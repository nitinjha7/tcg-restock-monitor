import json
import os
import sys
import time
import subprocess
import httpx
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MIN_PRICE = 15.0
DELAY_HOURS = 24
MAX_PAGES = 3
STORE_DELAY_SECS = 1.5
USER_AGENT = "Mozilla/5.0 (compatible; TCGMonitor/1.0)"

# --loop mode (free always-on polling on a public GitHub repo)
POLL_INTERVAL_SECS = 60          # gap between full polling cycles
COMMIT_INTERVAL_SECS = 20 * 60   # how often to commit state.json back to the repo
LOOP_MAX_SECONDS = 350 * 60      # exit cleanly before GitHub's 6h job cap, then re-dispatch

WATCH_GAMES = [
    "one piece", "lorcana", "pokemon", "pokémon", "riftbound",
    "gundam", "yu-gi-oh", "yugioh", "union arena",
]

KEEP_KEYWORDS = [
    "booster box", "booster case", "booster display", "hobby box", "hobby case",
    "elite trainer box", "etb", "booster bundle", "bundle", "blister", "mini tin",
    " tin", "booster pack", "build & battle", "build and battle", "starter deck",
    "case (", "12-box", "20-box", "6-box", "display",
    "booster box da", "set allenatore", "bustina",
]

EXCLUDE_TYPES = {
    "single", "single card", "single raw card", "graded tcg/ccg", "graded",
    "pop vinyl", "model kit", "miniatures", "figurines", "playmat", "deck box", "sleeves",
}

EXCLUDE_TITLE_FRAGMENTS = [
    "psa ", "cgc ", "ace ", "slab", " foil", "art rare",
    "/165", "/193", "/217", "/078",
    "funko", "pop!", "nendoroid", "warhammer", "games workshop",
    "astra militarum", "battleforce", "dragon shield", "ultra pro",
    "deck box", "playmat", "sleeve",
    "event entry", "draft entry", "event reservation", "tournament",
]

EXCLUDE_VENDORS = {
    "games workshop", "funko", "good smile company",
    "ultimate guard", "dragon shield", "ultra pro",
}

DISCORD_COLORS = {
    "RESTOCK": 0x00C851,
    "NEW_PREORDER": 0x33B5E5,
    "PRICE_DROP": 0xFF8800,
}
DISCORD_EMOJIS = {
    "RESTOCK": "🟢",
    "NEW_PREORDER": "🆕",
    "PRICE_DROP": "💸",
}
DISCORD_LABELS = {
    "RESTOCK": "RESTOCK",
    "NEW_PREORDER": "PREORDER",
    "PRICE_DROP": "PRICE DROP",
}

# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------

def _matches_any(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def _field(product: dict, key: str) -> str:
    """Lowercased string for a product field, tolerant of missing/null/list values.

    Shopify feeds sometimes return an explicit JSON null (e.g. body_html), so
    dict.get(key, "") is not enough — it returns None when the key is present.
    """
    value = product.get(key)
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(v) for v in value).lower()
    return str(value).lower()


def is_preorder(product: dict) -> bool:
    title = _field(product, "title")
    tags = _field(product, "tags")
    return (
        "preorder" in title or "pre-order" in title
        or "preordine" in tags or "preorder" in tags
    )


def is_sealed(product: dict) -> bool:
    ptype = _field(product, "product_type")
    title = _field(product, "title")
    vendor = _field(product, "vendor")

    if ptype in EXCLUDE_TYPES:
        return False
    if _matches_any(title, EXCLUDE_TITLE_FRAGMENTS):
        return False
    if vendor in EXCLUDE_VENDORS:
        return False

    variants = product.get("variants", [])
    if not variants:
        return False
    first_price = variants[0].get("price", "0.00")
    try:
        price_val = float(first_price)
    except (ValueError, TypeError):
        return False
    if first_price == "0.00" or price_val < MIN_PRICE:
        return False

    if not (_matches_any(ptype, KEEP_KEYWORDS) or _matches_any(title, KEEP_KEYWORDS)):
        return False

    if WATCH_GAMES:
        body = _field(product, "body_html")
        tags = _field(product, "tags")
        searchable = f"{title} {body} {tags}"
        if not _matches_any(searchable, WATCH_GAMES):
            return False

    return True


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def _fetch_feed(client: httpx.Client, base_url: str, label: str) -> list[dict]:
    """Paginate a Shopify products.json feed (root or per-collection)."""
    headers = {"User-Agent": USER_AGENT}
    products = []
    for page in range(1, MAX_PAGES + 1):
        url = f"{base_url}?limit=250&page={page}"
        try:
            resp = client.get(url, headers=headers)
        except Exception as exc:
            print(f"  [WARN] {label} page {page}: {exc}")
            break
        if resp.status_code != 200:
            print(f"  [WARN] {label} page {page}: HTTP {resp.status_code}")
            break
        try:
            data = resp.json()
        except Exception:
            print(f"  [WARN] {label} page {page}: invalid JSON")
            break
        page_products = data.get("products", [])
        products.extend(page_products)
        if len(page_products) < 250:
            break
    return products


def fetch_store(store: dict) -> list[dict]:
    """Fetch a store's products.

    If the store config lists `collections`, fetch each collection feed and
    dedupe by product id (a product can appear in several collections). This
    is how big general retailers (singles/board-games sorted first) expose
    their sealed stock without us paging past the cap. Otherwise fall back to
    the root /products.json feed.
    """
    domain = store["domain"]
    collections = store.get("collections")
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        if collections:
            products = []
            seen_ids = set()
            for handle in collections:
                base = f"https://{domain}/collections/{handle}/products.json"
                for p in _fetch_feed(client, base, f"{domain}/{handle}"):
                    if p["id"] not in seen_ids:
                        seen_ids.add(p["id"])
                        products.append(p)
            return products
        return _fetch_feed(client, f"https://{domain}/products.json", domain)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

STATE_FILE = "state.json"
_DEFAULT_STATE = {"products": {}, "delayed_queue": [], "known_product_ids": []}


def load_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # ensure all keys exist
        for k, v in _DEFAULT_STATE.items():
            data.setdefault(k, type(v)())
        return data
    except Exception:
        return {k: type(v)() for k, v in _DEFAULT_STATE.items()}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Event detection
# ---------------------------------------------------------------------------

def detect_events(
    domain: str,
    store_name: str,
    products: list[dict],
    state: dict,
    known_ids: set,
    emit: bool = True,
) -> list[dict]:
    events = []
    now_iso = datetime.now(timezone.utc).isoformat()
    state_products = state["products"]

    for product in products:
        product_id = str(product["id"])
        product_key = f"{domain}::{product_id}"
        handle = product.get("handle", "")
        title = product.get("title", "")
        image_url = ""
        images = product.get("images", [])
        if images:
            image_url = images[0].get("src", "")

        for variant in product.get("variants", []):
            variant_id = str(variant["id"])
            key = f"{domain}::{product_id}::{variant_id}"
            try:
                price = float(variant.get("price", "0"))
            except (ValueError, TypeError):
                price = 0.0
            available = bool(variant.get("available", False))

            variant_title = variant.get("title", "")
            display_title = title if variant_title in ("", "Default Title") else f"{title} — {variant_title}"

            base_event = {
                "domain": domain,
                "store_name": store_name,
                "title": display_title,
                "handle": handle,
                "price": price,
                "image_url": image_url,
                "available": available,
            }

            if key not in state_products and product_key not in known_ids:
                if emit and available and is_preorder(product):
                    events.append({**base_event, "type": "NEW_PREORDER"})
            elif key in state_products:
                prev = state_products[key]
                prev_available = prev.get("available", True)
                prev_price = float(prev.get("price", price))

                if emit and not prev_available and available:
                    events.append({**base_event, "type": "RESTOCK"})
                elif emit and price < prev_price * 0.95 and price > 0:
                    events.append({**base_event, "type": "PRICE_DROP", "old_price": prev_price})

            state_products[key] = {
                "available": available,
                "price": price,
                "title": display_title,
                "last_seen": now_iso,
            }
            known_ids.add(product_key)

    return events


# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------

def build_embed(event: dict) -> dict:
    etype = event["type"]
    emoji = DISCORD_EMOJIS[etype]
    label = DISCORD_LABELS[etype]
    color = DISCORD_COLORS[etype]
    domain = event["domain"]
    handle = event["handle"]
    price = event["price"]

    url = f"https://{domain}/products/{handle}"

    if etype == "PRICE_DROP":
        price_field = f"${price:.2f} (Was ${event['old_price']:.2f})"
    else:
        price_field = f"${price:.2f}"

    status = "Preorder" if etype == "NEW_PREORDER" else "In stock"

    embed: dict = {
        "title": f"{emoji} {label}: {event['title']}",
        "url": url,
        "color": color,
        "fields": [
            {"name": "Store", "value": event["store_name"], "inline": True},
            {"name": "Price", "value": price_field, "inline": True},
            {"name": "Status", "value": status, "inline": True},
        ],
        "footer": {"text": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")},
    }

    if event.get("image_url"):
        embed["thumbnail"] = {"url": event["image_url"]}

    return embed


def send_to_webhook(url: str, embed: dict) -> bool:
    try:
        resp = httpx.post(url, json={"embeds": [embed]}, timeout=10.0)
        if resp.status_code in (200, 204):
            return True
        print(f"  [WARN] Discord webhook returned {resp.status_code}")
        return False
    except Exception as exc:
        print(f"  [WARN] Discord webhook error: {exc}")
        return False


# ---------------------------------------------------------------------------
# Delayed queue
# ---------------------------------------------------------------------------

def enqueue_alert(state: dict, embed: dict) -> None:
    release_at = (datetime.now(timezone.utc) + timedelta(hours=DELAY_HOURS)).isoformat()
    state["delayed_queue"].append({"release_at": release_at, "payload": embed})


def release_due_alerts(state: dict, free_url: str) -> None:
    now = datetime.now(timezone.utc)
    remaining = []
    for entry in state["delayed_queue"]:
        try:
            release_at = datetime.fromisoformat(entry["release_at"])
        except Exception:
            remaining.append(entry)
            continue
        if release_at <= now:
            success = send_to_webhook(free_url, entry["payload"])
            if not success:
                remaining.append(entry)
        else:
            remaining.append(entry)
    state["delayed_queue"] = remaining


# ---------------------------------------------------------------------------
# Startup embed
# ---------------------------------------------------------------------------

def build_startup_embed(total_sealed: int, num_stores: int) -> dict:
    return {
        "title": "✅ TCG Monitor Online",
        "description": (
            f"Now tracking **{total_sealed} sealed products** across **{num_stores} stores**.\n"
            "Alerts will fire from the next run onwards."
        ),
        "color": 0x7289DA,
        "footer": {"text": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")},
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def commit_state() -> None:
    """Commit state.json back to the repo. No-op outside GitHub Actions."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    try:
        subprocess.run(["git", "add", STATE_FILE], check=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0:
            subprocess.run(["git", "commit", "-m", "update state [skip ci]"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("  state committed")
    except Exception as exc:
        print(f"  [WARN] git commit failed: {exc}")


def run_once(stores: list, state: dict, known_ids: set,
             live_url: str, free_url: str) -> tuple[int, int]:
    """One full polling cycle: fetch all stores, detect events, alert, save.

    Returns (events_emitted, total_sealed). On the first cycle (empty state)
    it only populates state and sends a single "online" message — alerts begin
    from the second cycle to avoid a flood.
    """
    first_run = not state["products"]
    all_events: list[dict] = []
    total_sealed = 0

    for i, store in enumerate(stores):
        name = store["name"]
        if i > 0:
            time.sleep(STORE_DELAY_SECS)
        print(f"Fetching {name} ({store['domain']})...")
        try:
            products = fetch_store(store)
            sealed = [p for p in products if is_sealed(p)]
            total_sealed += len(sealed)
            print(f"  {len(products)} products fetched, {len(sealed)} sealed kept")
            events = detect_events(
                store["domain"], name, sealed, state, known_ids, emit=not first_run
            )
            all_events.extend(events)
        except Exception as exc:
            print(f"  [ERROR] {name}: {exc}")

    state["known_product_ids"] = list(known_ids)

    if first_run:
        print(f"\nFirst run — tracking {total_sealed} sealed products across {len(stores)} stores.")
        if live_url:
            send_to_webhook(live_url, build_startup_embed(total_sealed, len(stores)))
    else:
        print(f"\n{len(all_events)} event(s) detected.")
        for event in all_events:
            embed = build_embed(event)
            print(f"  [{event['type']}] {event['title']} @ {event['store_name']}")
            if live_url:
                send_to_webhook(live_url, embed)
            if free_url:
                enqueue_alert(state, embed)

    if free_url:
        release_due_alerts(state, free_url)

    save_state(state)
    return len(all_events), total_sealed


def main() -> None:
    loop_mode = "--loop" in sys.argv

    with open("stores.json", "r", encoding="utf-8") as f:
        stores = json.load(f)

    state = load_state()
    known_ids: set = set(state["known_product_ids"])
    live_url = os.environ.get("DISCORD_WEBHOOK_LIVE", "")
    free_url = os.environ.get("DISCORD_WEBHOOK_FREE", "")

    if not loop_mode:
        events, total = run_once(stores, state, known_ids, live_url, free_url)
        commit_state()
        print(f"State saved. {total} sealed products tracked across {len(stores)} stores.")
        return

    # Always-on loop: poll continuously, commit periodically, then exit before
    # the 6h job cap so the workflow can re-dispatch a fresh job.
    print(f"Loop mode: polling every ~{POLL_INTERVAL_SECS}s for up to {LOOP_MAX_SECONDS // 60} min.")
    start = time.time()
    last_commit = 0.0
    cycle = 0
    while time.time() - start < LOOP_MAX_SECONDS:
        cycle += 1
        print(f"\n===== cycle {cycle} @ {datetime.now(timezone.utc).isoformat()} =====")
        try:
            run_once(stores, state, known_ids, live_url, free_url)
        except Exception as exc:
            print(f"[ERROR] cycle failed: {exc}")
        if time.time() - last_commit > COMMIT_INTERVAL_SECS:
            commit_state()
            last_commit = time.time()
        time.sleep(POLL_INTERVAL_SECS)

    commit_state()  # final snapshot before handing off to the next job
    print("Loop window elapsed — exiting for re-dispatch.")


if __name__ == "__main__":
    main()
