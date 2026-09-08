# Launch Plan — from £0 to first revenue

Written 2026-09-08. Everything here is based on measured data from this repo, not estimates.
Where a number is a guess, it says so.

---

## The situation, honestly

**What works:** the monitor is genuinely good. 1,820 sealed products across 13 shops, a full
cycle every 57s, **828 real alerts fired over the last 70 days** (11.8/day — 374 restocks,
430 price drops, 24 preorders, median item value ~£100).

**Why it has earned £0:** every one of those 828 alerts went to a private Discord webhook with
no members. There is no public channel, no site (until now), and no way for anyone to find it.

**Why the affiliate plan in `STRATEGY.md` cannot fix that** — all verified 2026-09-08:

| Check | Result |
|---|---|
| Monitored stores with any affiliate program | **2 of 13** (Total Cards, The Card Vault) |
| Total Cards terms | 1% commission, **£25 minimum payout** — ~£2,500 of sales before you're paid |
| Share of alert volume from Total Cards | **4.3%** (36 of 828) |
| PTC Collectibles (10%) | Requires Shopify Collabs: **1,000 followers**, reportedly closed to new creators |
| Broad scan of 24 major TCG retailers | **No overlap** between "public Shopify feed" and "joinable affiliate program" |

Your top five alert sources — Pack Fresh, Japan2UK, 401 Games, Skybox CT, Stomping Grounds —
are **78% of all volume and pay nothing at all**. Affiliate links here would earn roughly
nothing no matter how well they were built.

**Therefore: revenue comes from selling access, not commissions.** One subscriber at £5/month
beats five booster boxes sold via Total Cards, arrives with no payout threshold, and is 100%
margin.

---

## What you're actually competing against

There is a **free Discord with ~96,000 members** covering 100+ retailers across all TCGs. You
will never beat it on US big-box Pokémon restocks. Don't try.

But several **paid** restock apps also exist (Restock Pulse, TCG Restock, PokeWatcher), which
proves people pay for this — just not for a worse copy of the free giant.

### Where you can actually win

From your own in-stock data (547 items live right now):

- **Japanese & Korean import sealed** — Japan2UK alone is 208 in-stock items; Elemental Cards
  carries Korean booster boxes. The big US monitors do not cover this.
- **Non-Pokémon TCGs** — Yu-Gi-Oh! 74, Union Arena 39, Lorcana 32, One Piece 32, Gundam 12,
  Riftbound 5. Most restock services are Pokémon-only.
- **Independent shops** in the UK, EU and Canada, not Walmart/Target.

**Positioning to use everywhere:**

> Sealed restocks from the shops and games the big monitors ignore — Japanese and Korean
> imports, One Piece, Union Arena, Gundam and Lorcana, from independent shops in the UK, EU
> and Canada.

Note: 69% of your alerts are USD-priced, so do **not** claim to be a "UK/EU feed" — the data
doesn't support it and people will notice.

---

## Step 1 — You, ~20 minutes. This is the only thing blocking everything else.

The board is live at **https://tcgstockboard.github.io/** and the Discord join button is
wired to the TCG Alerts `#free-feed` invite. Only Telegram is outstanding.

### 1a. Telegram (5 min — do this first, it's the easiest to grow)
1. Message **@BotFather** → `/newbot` → copy the **bot token**.
2. Create a **public channel** (e.g. `@tcgstockboard`). Add the bot as **admin** with
   *Post Messages*.
3. Add repo secrets (Settings → Secrets and variables → Actions):
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (use `@yourchannel`).

### 1b. Discord — done
Server `TCG Alerts` with `#free-feed` and `#paid-alerts`, both webhooks live since 2026-06-29.
Invite `https://discord.gg/dCrGMB52BE` is wired into the board.

**Outstanding:** during the growth phase, set `DISCORD_WEBHOOK_PUBLIC` to the `#free-feed`
webhook and remove `DISCORD_WEBHOOK_FREE`. That makes the free feed instant instead of 24h
delayed — the delay protects a paid tier that has no customers yet, and gives every new joiner
a first impression of day-old, already-sold-out alerts. Reverse it when paid launches.

Full per-channel detail is in `BROADCAST_SETUP.md`. Bluesky and Mastodon are worth adding later
but are not on the critical path.

---

## Step 2 — Your 3–5 hrs/week, weeks 1–8

The goal is **300 free members**. That is the number that makes a paid tier viable.

**The rule that keeps you alive:** never cold-drop a Discord invite. Most TCG communities ban
it on sight, and a banned account ends the project. Link the **site**, not the server — a free
public tool is tolerated where a server ad is not. Read each community's rules before posting;
I could not verify them individually.

**Weekly rhythm:**

| Time | What |
|---|---|
| ~2 hrs | Genuinely participate in TCG communities — answer "where can I buy X at RRP" questions with a real, specific answer. Link the board only when it directly answers the question. |
| ~1 hr | Post one genuinely useful thing: "Korean booster boxes back in stock at 4 shops this week", with the data. Not an ad. |
| ~30 min | List the Discord on **Disboard** and **Discadia** and bump manually. Never use auto-bump bots — they are against ToS and get servers banned. |
| ~30 min | Reply to everyone who joins. Early members who feel heard are what makes this spread. |

**Best-fit communities** (verify rules yourself before posting): One Piece TCG, Union Arena,
Lorcana and Japanese-import collector communities — you have real coverage there and almost no
competition, unlike Pokémon where the 96k server dominates.

**Never:** mass-DM, scrape members from other servers, buy followers, or spam subreddits.

---

## Step 3 — Charge (once ~300 free members, realistically week 8–12)

Use **Whop** — it handles Stripe, auto-assigns the Discord role on payment, and handles
cancellations. Free to start, takes a cut per sale.

- **Free tier:** 24h-delayed alerts + the public board. Already built (`DISCORD_WEBHOOK_FREE`).
- **Paid tier, £5/month:** instant alerts. Already built (`DISCORD_WEBHOOK_LIVE`).

The delay is the entire pitch, and the monitor already implements it. Put a line on every free
alert: *"Paid members saw this 24 hours ago, while it was still in stock."*

Price at £5. Undercutting the $6–10 US services is the right call while you're small and
unproven.

---

## Honest numbers

- **First paying customer: 6–12 weeks.** Not days. The constraint is audience trust.
- 300 free members converting at 2–5% ≈ **£30–75/month** initially.
- Getting past ~£200/month means 1,000+ members — realistically 6–12 months, and only if the
  import/non-Pokémon niche proves out.
- **This will not produce meaningful money quickly.** Anyone claiming otherwise is guessing.

The single highest-risk assumption is that people will pay for *import and non-Pokémon* sealed
alerts. Test it cheaply: if the free feed hasn't reached ~150 members by week 6, the niche is
wrong — and the answer is to change the shop list, not to build more features.

---

## What's already done

- Coverage widened 1,538 → 1,820 sealed products; cycle time 92s → 57s.
- Two filter bugs fixed that were silently dropping real product (`"ace "` matched
  "Sp**ace** Juggler Booster Box"; `"sleeve"` matched 49 real "Sleeved Booster Pack" listings).
- `MIN_DROP_PCT` raised to 10 — 5–9% moves were 45% of all price drops and rarely actionable.
- Public board live on GitHub Pages, rebuilt from `docs/feed.json` every cycle.
- Alert history now retained in `state.recent_events` — the dataset any future SEO pages
  would be built from.
