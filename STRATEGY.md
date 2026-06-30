# TCG Restock Monitor — Product, Quality & Distribution Strategy

## Part 1 — The Product: Is It Real, Saturated, Will People Pay?

**Demand: proven, not speculative.**
- PokeNotify has ~23,000 *paying* members. PKMNTCGDeals has 90,233 free members (6 years running). PokePings has ~14,800 on its free tier alone.
- Pricing is established: budget alert services $3–10/mo (Poke Alerts $5.99, PokePings $8.99, The Hobby Bin $2.99), premium cook groups $20–75/mo (Divine Cards $35).

So "will people pay?" — yes, demonstrably, at scale. That question is settled.

**Saturation: severe — but only in one lane.** Almost every incumbent monitors big-box US retailers — Walmart, Target, Costco, Best Buy, GameStop, Pokémon Center. Competing there means fighting 90k-member, 6-year-old operations. You lose.

**Our accidental moat:** this monitor watches **independent Shopify shops** (Total Cards, Ripperholics, Otakura…), many UK/EU, across **multiple games** (Pokémon, One Piece, Lorcana, Riftbound, Gundam, Union Arena). Nobody owns that. The US giants don't cover independent UK/EU shops and are Pokémon-mono-focused.

### The Niche — Committed

> **"Every restock & RRP drop across independent UK/EU TCG shops — Pokémon, One Piece, Lorcana and more — in one feed. The drops the big US monitors miss."**

Why this wins:
- Less competition (not fighting PokeNotify on Target)
- Infrastructure already built and stores already confirmed working
- Multi-game = broader audience than Pokémon-only
- Independent shops sell at RRP → serves collectors/deal-hunters (buy before scalpers) — a larger, less-saturated audience than hardcore US flippers; resellers are a paying sub-segment, not the whole market

**Verdict:** Viable and genuinely differentiated if we commit to this niche. Non-viable as "another Pokémon-US restock server."

---

## Part 2 — The Product: Quality Gaps to Fix (Prioritised)

The current build is a solid skeleton but not premium yet. Gaps in priority order:

1. **Speed — #1 weakness.** A 5-minute GitHub Actions cron is slow and unreliable (GH delays scheduled jobs under load). Premium services ping in seconds. For sealed product that sells out in minutes, 5 min late = useless. **Fix:** move to an always-on host (Fly.io / Railway / a $5 VPS / Cloudflare Workers) polling every 30–60s.
2. **Coverage:** 8 stores → 40+ independent UK/EU shops. It's just data (stores.json) — cheap to expand, directly widens the moat.
3. **Per-user filtering:** Discord roles + reaction menu so users pick their games/products and only get pinged for those. Premium-grade UX and a natural paywall later.
4. **Richer alerts:** price history, "sold out in X min" stats, stock levels where exposed, RRP-vs-scalper context.
5. **A public website:** doubles as the SEO engine (see Part 3).

---

## Part 3 — Distribution: The Automated Growth Engine

**Core principle:** build ONE data engine, fan it out to many discovery surfaces automatically. The monitor already produces the data — broadcast it everywhere.

### Engine 1 — Multi-channel feed broadcast (build now)
Pipe the same alerts to public owned channels: a public Discord feed, an X/Twitter auto-poster, a Telegram channel, optionally Bluesky. "Restock Twitter" is a proven organic-discovery machine. One monitor → many funnels, zero extra labour after setup.

### Engine 2 — Programmatic SEO site
Generic pSEO is dying — except when built on proprietary data competitors can't replicate, which is exactly what this monitor produces. Auto-generate pages from restock history: *"[Product] UK restock tracker,"* *"Where to buy [set] at RRP UK."* These rank for long-tail "X restock UK" searches → organic traffic → Discord joins, 24/7, automatically. There is confirmed UK search demand (e.g., tcgranger.co.uk ranks for "buy Pokémon at RRP UK").

### Engine 3 — Discord directories
List on **Disboard (4M monthly users)** and **Discadia (2M)** and bump every 2h. Use a *bump-reminder* bot — not auto-bumpers that violate ToS and get the server banned.

### Engine 4 — Affiliate review-site placement
Sites like tcgdropradar.com and cook-groups.com rank these servers and monetize via affiliate links. Offer them a cut to get listed — instant borrowed authority and backlinks.

### Engine 5 — Referral loop
Invite-tracking: members who invite others earn perks/roles. Self-reinforcing and costs nothing.

### Engine 6 — Micro-influencer seeding
Free access + affiliate cut to small UK Pokémon/TCG YouTubers and TikTokers (5k–50k followers). One right creator beats 1,000 cold posts. The affiliate cut makes it worth their effort automatically.

### Red lines — what NOT to automate
Mass-DMing, scraping other servers' members, fake accounts/engagement, spamming subreddits, banned auto-bump bots. "Growth hacks" that violate ToS kill the account everything is built on. Growth happens on owned surfaces + SEO + genuine seeding only.

---

## Part 4 — Revenue: Fast + Realistic

### Immediate revenue: affiliate links (no subscribers required)
This is the honest fastest path. Wrap every buy-link in every alert with affiliate tags:

| Program | Commission | Notes |
|---|---|---|
| Total Cards | 1%–5% | One of our 8 monitored stores, UK flagship |
| PTC Collectibles | 10% | Highest rate found |
| TCGplayer | 3.5% | Large US marketplace |

Earn on every purchase the free audience makes — from day one, invisibly, with zero paid subscribers. Perfectly aligned with the free-first growth strategy.

### Later revenue: premium instant tier
Via **Whop.com** (handles Stripe + auto-assigns Discord role on payment, handles cancellations automatically).

- **Free tier:** 24h delayed alerts, public feed (funnel)
- **Premium ($6–10/mo):** instant alerts + per-product/game filters + faster polling
- Introduce only after audience + proof of value is established

Every free-feed alert should include a FOMO hook: *"Paid members saw this 24h ago while it was in stock → [join link]"*

### Honest numbers
Affiliate trickle starts almost immediately and scales with free audience size. A free feed of 300–500 engaged members realistically converts 3–5% to a later paid tier (~£150–300/mo) plus affiliate passive income. This is a weeks-to-months trajectory, not days. No "sure shot" exists — but this is the evidenced, realistic path.

---

## Part 5 — Build Order (Highest ROI First)

| Phase | What | Why |
|---|---|---|
| **Now — Phase 1** | Affiliate-link wrapping in alerts | Revenue from day one, no audience needed |
| **Now — Phase 1** | X/Twitter + Telegram broadcast output | Automated distribution engine, zero ongoing labour |
| **Now — Phase 1** | Expand stores to 30–40 UK/EU shops | Widens moat, purely a data change |
| **Now — Phase 1** | Free-feed FOMO CTA in every alert | Conversion hook for when premium launches |
| **Phase 2** | Always-on faster hosting (30–60s polling) | Premium product quality unlock |
| **Phase 2** | Per-user game/product role filters | Reduces noise, increases retention |
| **Phase 2** | Programmatic SEO site from restock history | 24/7 organic discovery engine |
| **Phase 3** | Whop integration for paid tier | Monetise built audience |

**Action required from you (only you can do these — they need your identity):**
1. Sign up for the [Total Cards affiliate program](https://totalcards.net/pages/affiliates)
2. Sign up for the [TCGplayer affiliate program](https://docs.tcgplayer.com/docs/tcgplayer-affiliate-program)
3. Sign up for [PTC Collectibles affiliate](https://ptccollectibles.com/pages/affiliate)

Once you have your affiliate IDs, I wire the links into the monitor alerts.

---

## Sources
- [Best Pokémon Restock Discords 2026 — TCG Drop Radar](https://tcgdropradar.com/)
- [Top Pokémon Restocks & Reselling Discords — Sole Radar](https://cook-groups.com/pokemon-discords/)
- [PikaNotify](https://pikanotify.com/)
- [The Hobby Bin restock guide](https://thehobbybin.com/blogs/pokemon-tcg-guides/pokemon-card-restock-alerts-discord)
- [PKMNTCGDeals Discord](https://discord.com/invite/pkmntcgdeals)
- [Best US Cook Groups 2026 — cookgroups.net](https://cookgroups.net/us-cook-groups/)
- [Best reselling Discord servers — Whop](https://whop.com/blog/best-reselling-discord-servers/)
- [Total Cards Affiliate Program](https://totalcards.net/pages/affiliates)
- [TCGplayer Affiliate Program](https://docs.tcgplayer.com/docs/tcgplayer-affiliate-program)
- [PTC Collectibles Affiliate](https://ptccollectibles.com/pages/affiliate)
- [Disboard growth guide](https://disboard.uk/)
- [Awesome Discord Growth tools](https://github.com/CommunityOne-io/awesome-discord-growth)
- [Programmatic SEO — when it still works](https://www.rankscience.com/blog/how-to-grow-your-traffic-with-programmatic-seo)
- [Best places to buy Pokémon at RRP UK — TCG Ranger](https://tcgranger.co.uk/retail-stock-rrp/)
