import json
import os
import time
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

def fetch_store(domain: str) -> list[dict]:
    products = []
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for page in range(1, MAX_PAGES + 1):
            url = f"https://{domain}/products.json?limit=250&page={page}"
            try:
                resp = client.get(url, headers=headers)
            except Exception as exc:
                print(f"  [WARN] {domain} page {page}: {exc}")
                break
            if resp.status_code != 200:
                print(f"  [WARN] {domain} page {page}: HTTP {resp.status_code}")
                break
            try:
                data = resp.json()
            except Exception:
                print(f"  [WARN] {domain} page {page}: invalid JSON")
                break
            page_products = data.get("products", [])
            products.extend(page_products)
            if len(page_products) < 250:
                break
    return products


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

def main() -> None:
    with open("stores.json", "r", encoding="utf-8") as f:
        stores = json.load(f)

    state = load_state()
    first_run = not state["products"]
    known_ids: set = set(state["known_product_ids"])

    all_events: list[dict] = []
    total_sealed = 0

    for i, store in enumerate(stores):
        name = store["name"]
        domain = store["domain"]
        if i > 0:
            time.sleep(STORE_DELAY_SECS)
        print(f"Fetching {name} ({domain})...")
        try:
            products = fetch_store(domain)
            sealed = [p for p in products if is_sealed(p)]
            total_sealed += len(sealed)
            print(f"  {len(products)} products fetched, {len(sealed)} sealed kept")
            events = detect_events(
                domain, name, sealed, state, known_ids, emit=not first_run
            )
            all_events.extend(events)
        except Exception as exc:
            print(f"  [ERROR] {name}: {exc}")

    state["known_product_ids"] = list(known_ids)

    live_url = os.environ.get("DISCORD_WEBHOOK_LIVE", "")
    free_url = os.environ.get("DISCORD_WEBHOOK_FREE", "")

    if first_run:
        print(f"\nFirst run — tracking {total_sealed} sealed products across {len(stores)} stores.")
        if live_url:
            send_to_webhook(live_url, build_startup_embed(total_sealed, len(stores)))
    else:
        print(f"\n{len(all_events)} event(s) detected.")
        for event in all_events:
            embed = build_embed(event)
            etype = event["type"]
            print(f"  [{etype}] {event['title']} @ {event['store_name']}")
            if live_url:
                send_to_webhook(live_url, embed)
            if free_url:
                enqueue_alert(state, embed)

    if free_url:
        release_due_alerts(state, free_url)

    save_state(state)
    print(f"State saved. {total_sealed} sealed products tracked across {len(stores)} stores.")


if __name__ == "__main__":
    main()
