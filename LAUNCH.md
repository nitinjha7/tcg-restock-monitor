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

### 1a. Telegram — done
Public channel **https://t.me/tcgstockboard**, `@tcg_stock_alerts_bot` posting as admin.
`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set and the board links to it.

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

## Step 2 — Getting to 300 members

**Recruit distributors, not members.** Converting 300 people one at a time is the slowest
path with the lowest ceiling. Five server owners saying yes gets you there faster than five
hundred individual pitches. The official One Piece Card Game Discord alone has ~107,000
members, in a game the big Pokemon monitors don't cover.

### 2a. Feed syndication — the highest-leverage play

Every TCG Discord wants a `#deals` channel with real content and has nobody to staff it. You
have a live feed. `DISCORD_WEBHOOK_PUBLIC` now accepts **multiple webhooks** (comma- or
whitespace-separated), so onboarding a partner server is one config change.

The pitch — sent to a server owner or mod, not posted publicly:

> I run a sealed-restock monitor across 13 independent shops — Japanese/Korean/Chinese
> imports, One Piece, Union Arena, Lorcana, plus Pokemon. Roughly 12 alerts a day with live
> prices and buy links. I'd like to pipe it into your server free, live. It's one webhook,
> zero work for you, and your members get restock alerts nobody else is posting. All I ask
> is a credit line in the channel topic.

Give first, ask nothing beyond attribution. Naive "let's cross-promote" requests are ignored;
a free working feed is not. One 2,000-member server converting at 2–5% is 40–100 members, so
**five yeses clears 300**.

To add a partner: append their webhook URL to the `DISCORD_WEBHOOK_PUBLIC` secret, separated
by a space or comma. A dead partner webhook warns and is skipped — it never blocks the others.

### 2b. Measure it, don't guess

Discord reports **uses per invite link**. Create a separate never-expiring invite for every
source — Reddit, Telegram, the board, and one per partner server — then Server Settings →
Invites shows exactly where members come from.

Within two weeks you'll know which channel works and can stop doing the rest. Without this
you're guessing, and guessing is how the 3–5 hrs/week gets wasted.

### 2c. Publish the data, not the service

"Join my Discord" is removed as spam. A genuine finding is upvoted, and the board link becomes
a citation rather than an ad. You have 70 days of restock history across 13 shops that nobody
else has — that is publishable content:

- "I tracked every Korean booster box across 13 UK/EU shops for 70 days — here's where they're
  actually cheapest"
- "Which sealed products restock most often, and which never come back"
- "What Chinese-language slim booster boxes actually cost across 4 shops"

### 2d. Directory listings — passive and permanent

List the server on **Disboard**, **Discadia**, **Top.gg** and **Discord.me**. These rank on
Google for searches like "TCG restock discord" that your own site won't touch for months —
you're borrowing their domain authority. Write a real description with keywords, add a banner
and icon, and bump manually. **Never use auto-bump bots** — against ToS, and they get servers
banned.

### 2e. Be the answer to the recurring question

Every TCG community has someone asking weekly "where can I still get X at RRP?" You can answer
that with live, correct, specific data. That is being useful, not promoting, and it's the only
form of self-promotion these communities reliably tolerate. Read each community's rules first;
they vary and I could not verify them individually.

**Best-fit targets** — where you're differentiated and the 96k Pokemon server isn't competing:
One Piece TCG, Union Arena, Lorcana, and Japanese/Korean/Chinese import collector communities.

**Never:** mass-DM, scrape members from other servers, buy followers, or spam subreddits. A ban
ends the project.

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
