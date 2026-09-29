# Setup guide for your agent

You (the agent) are setting up **xreplies**, a local finder for X posts worth replying to, plus the playbook it comes from. Work through the steps in order, run the commands yourself, and only stop to ask the user for things only they can do (sign-ins, their handle, their topics). Explain costs before spending money.

Read `PLAYBOOK.md` first so you understand what the user is trying to do. Read `xreplies/docs/FRAMEWORK.md` for why each filter exists.

## 1. Install treg (data access, pay per call)

treg.to gives one token access to X search and profile data. The user pays per call from a prepaid balance. A Fetch in the finder costs about 1 to 3 cents.

```
curl -fsSL https://treg.to/install.sh | sh
treg login
treg balance
```

- `treg login` opens a browser. The user signs in; the first login creates their account.
- If the balance is 0, ask the user to add credit (`treg topup`, $5 to $10 is plenty to start).
- Check it works: `treg call anyapi.x.user.profile --method POST --data '{"handle":"<their handle>"}'` should return their profile.
- Needs Python 3.12+ (the installer handles it).

## 2. Configure

Create `xreplies/config.local.json`. Only put what differs from `config.example.json` (your file is merged on top of it):

```json
{ "handle": "their_x_handle_without_@" }
```

Then ask the user what they post about. The two default topics are "Frontier labs" (models, labs, launches) and "Agents & vibe coding". If their niche is different, set their own topics and keywords:

```json
{
  "handle": "janedoe",
  "topics": {
    "rising": { "label": "AI design", "keywords": ["midjourney", "\"nano banana\"", "figma ai"] },
    "agents": { "label": "Indie SaaS", "keywords": ["\"build in public\"", "MRR", "\"first customer\""] }
  }
}
```

Keyword tips: X search syntax works (quotes for phrases, `OR` between alternatives). Avoid single words that mean other things (the playbook has examples: "grok", "muse", "gemini"). Keep 6 to 10 keywords per topic.

Thresholds (views, ratios, follower minimums) are in `config.example.json` under `rules`. Leave the defaults unless the user asks; they come from the research.

## 3. Start the finder

```
./xreplies/start.sh
```

It serves http://127.0.0.1:5191 on the user's machine only and fetches nothing until they press **Fetch**. Stop with `./xreplies/stop.sh`.

Three tabs: **Rising** (posts climbing fast on their topics, with topic chips and a "+ Topic" button), **Followers** (latest posts from people who follow them) and **New builders** (fresh builders saying hi on connect threads). The ⚙ gear in each tab shows and edits its keywords and rules, with how many posts each rule removed.

## 4. Load the side-panel extension (Chrome, or any Chromium browser)

The user does this by hand:

1. Open `chrome://extensions` (Comet: `comet://extensions`, Arc/Brave: same idea).
2. Turn on **Developer mode**.
3. **Load unpacked** → choose the `xreplies/extension` folder.
4. Pin the xreplies icon and click it. The panel opens beside X, and clicking a post opens it in the tab next to the panel.

The finder (step 3) must be running for the panel to load posts.

## 5. Optional: SuperX (scheduling and analytics)

Not needed for the finder. Useful for scheduling posts and reading reply stats. If the user has SuperX:

```
claude mcp add --transport http superx https://api.superx.so/v1/mcp --header "Authorization: Bearer <SUPERX_API_KEY>"
```

(or `npm install -g superx-cli` then `superx login`). Key from https://app.superx.so/account?tab=api.

## 6. Day to day

- The user presses Fetch, replies to what's on the list, and presses **Skip** with a reason on anything that doesn't belong.
- When they say **"review my skips"**, follow `xreplies/docs/SKIP-REVIEW.md` and propose new filters.
- When they want to change keywords or rules, edit `config.local.json` (or they can use the Filters tab).
- To re-tune thresholds for their niche, run `research/velocity-tracker/tracker.py` for an evening (≈ $1), then `calibrate.py`.

## Rules for you

- Never invent numbers in posts you help write. Use their real numbers.
- Don't post, follow, or DM on the user's behalf unless they explicitly ask.
- Keep their data local. `xreplies/data/` and `config.local.json` are theirs and should never be committed or shared.
