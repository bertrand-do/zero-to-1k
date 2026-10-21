# Onboarding guide for your agent

You (the agent) are setting up **zero-to-1k** for the user: a local finder for X posts worth replying to, with a Chrome side panel. Your job is to get them from nothing to their **first Fetch on the Mutuals tab**. That first Fetch is the finish line of setup.

How to run this guide:

- Go one step at a time, in order. Run every command yourself. Before each step, tell the user in one or two plain sentences what it is and why.
- Stop and wait only for what the user must do by hand: signing in to treg, adding credit, giving their X handle and topics, and loading the extension in Chrome. At each of those, ask them to reply "done" (or paste what they see), then confirm it worked before you move on.
- Explain costs before anything spends money.
- Keep messages short. The user is not necessarily technical.

For background, read `PLAYBOOK.md` (what the user is trying to do) and `finder/docs/FRAMEWORK.md` (why each filter exists). You don't need to summarise them to the user.

## 0. Get the repo

If you are not already inside a clone of this repo (no `AGENTS.md` and `finder/` next to you), clone it into the current folder and work from there:

```
git clone https://github.com/bertrand-do/zero-to-1k
cd zero-to-1k
```

Check the tools:

- `python3 --version` must be 3.12 or newer. If it's missing or older, install it (macOS: `brew install python@3.12` or the installer from python.org; Linux: the package manager) or tell the user exactly what to install.
- `zsh` must exist (`command -v zsh`). It's the default on macOS. On Linux, install it with the package manager. On Windows, use WSL.
- `git` must exist (it did if the clone worked).

## 1. Connect treg.to (the data source)

treg.to gives one token access to X search and profile data. The user pays per call from a prepaid balance. A Fetch in the finder costs about 1 to 3 cents.

If `treg` is not installed (`command -v treg`), install it:

```
curl -fsSL https://treg.to/install.sh | sh
```

Before logging in, tell the user this, in your own words:

> If you don't have a treg account yet, sign up through Bertrand's referral link first: https://treg.to/?ref=bdiouly-5h5gs. You get a $5 bonus when you add $10 (Bertrand gets a small referral credit too). If you already have an account, skip this.

Wait for them, then run:

```
treg login
treg balance
```

- `treg login` opens a browser. The user signs in there. Wait until they say it's done.
- If the balance is 0, ask them to add $10 (`treg topup`, or from the treg.to site). Tell them what it buys: a Fetch costs about 1 to 3 cents, so $10 lasts a long time. The Watched and Trending tabs check in the background and spend a little credit; they can be switched off in the panel with one button.
- Don't continue until the balance is above 0.

## 2. Their handle and topics

Ask for their X handle (without the @). Check it with one profile call:

```
treg call anyapi.x.user.profile --method POST --data '{"handle":"<their handle>"}'
```

If it returns their profile, show them their name and follower count so they know it's the right account, and write down that follower count as their "before" number. If it fails, check the spelling with them.

Create `finder/config.local.json`. Only put what differs from `finder/config.example.json` (your file is merged on top of it):

```json
{ "handle": "their_x_handle_without_@" }
```

Then ask what they post about. The two default Rising topics are "Frontier labs" (models, labs, launches) and "Agents & vibe coding". Offer those, or set their own topics and keywords:

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

Thresholds (views, ratios, follower minimums) are in `finder/config.example.json` under `rules`. Leave the defaults unless the user asks; they come from the research. Days on the Mutuals tab and the reply counter use the computer's local timezone; to use another one, add `"timezone": "America/New_York"` (any IANA name) to `config.local.json`.

## 3. Start the finder

```
./finder/start.sh
```

Then check it answers: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5191` should print 200. If it doesn't, read `finder/data/finder.log` and fix what it says. The usual causes are a missing `config.local.json`, treg not on the PATH, or another program on port 5191.

The finder serves http://127.0.0.1:5191 on the user's machine only and fetches nothing until they press **Fetch**. Stop it with `./finder/stop.sh`.

## 4. Load the side panel extension

The user does this by hand, so give them clear steps. First print the absolute path of the extension folder for them to pick (run `cd finder/extension && pwd` and show the result).

Chrome:

1. Open a new tab and go to `chrome://extensions`.
2. Turn on **Developer mode** with the toggle in the top right corner.
3. Click **Load unpacked**.
4. Pick the folder at the path you printed (the `extension` folder itself, the one that contains `manifest.json`).
5. Click the puzzle piece icon in the toolbar and pin **Zero to 1k**.
6. Open x.com and click the Zero to 1k icon. The panel opens next to X, and clicking a post opens it in the tab beside the panel.

Other Chromium browsers work the same way. Brave, Edge and Arc also open `chrome://extensions` (or use `brave://extensions` / `edge://extensions`); Comet uses `comet://extensions`. In Edge, Developer mode is in the left sidebar. Safari and Firefox are not supported.

Ask them to reply "done" once the panel is open. Troubleshooting:

- **"Manifest file is missing or unreadable"**: they picked the wrong folder (often the repo root or `finder/`). They need the `extension` folder that contains `manifest.json`.
- **Panel says "The finder isn't running" or stays empty**: the finder from step 3 is not running. Run `./finder/start.sh` again and check http://127.0.0.1:5191.
- **No icon in the toolbar**: it's under the puzzle piece; pin it.
- **The icon opens a narrow window instead of a side panel**: that's the fallback for browsers without side panel support. It works the same way.

## 5. The first Fetch (the activation point)

Tell the user to open the **Mutuals** tab and press **Fetch**. Explain first: the very first Mutuals Fetch looks back 7 days of comments on their posts, so it can take a minute or two and costs a few cents. Later Fetches only look at the last 48 hours and are quicker.

When the list loads, ask them to reply to the first person on it, right now, on that person's own post. That's the habit the whole thing is built on: pay back the people who already show up for you.

Then have them open **Rising** and press **Fetch** there too. Those are posts on their topics that are climbing fast; replying early borrows their audience.

Confirm they see results on both tabs. If a tab is empty:

- Check the handle in `config.local.json` is right (case doesn't matter, no @).
- Mutuals is empty if nobody commented on their posts or answered their replies in the last 48 hours. That's normal for a new or quiet account. Point them to **Rising** and **Followers** instead; replying there is what gets the first comments.
- Rising is empty if nothing on their topics is climbing right now. Try again in 20 to 30 minutes, or widen the keywords (the ⚙ gear on the tab shows how many posts each rule removed).
- If a Fetch fails, run `treg balance` and read `finder/data/finder.log`.

## 6. Wrap up

Give them a short daily routine:

1. Open the panel next to X and press Fetch on **Mutuals** first. Reply to everyone you owe.
2. Then **Rising**: reply early to the posts climbing on your topics.
3. When you have time, **Followers** and **Following**. Press **Skip** with a reason on anything that doesn't belong, so the filters learn.

How to stop and start: `./finder/stop.sh` and `./finder/start.sh` from the repo folder (or just ask your agent). The extension only works while the finder is running.

Finish by inviting them to DM a screenshot of their first Fetch, and later their before and after, to Bertrand on X: https://x.com/BertrandDiouly. Remind them of the "before" follower count you noted in step 2.

## The tabs

- **Mutuals**: a "who do I owe a reply" queue. People who commented on your posts (green) or answered your replies (grey) in the last 48 hours, most recent first, with one fresh post each to reply on. Real mutuals (you follow each other) come first, because X's ranking code gives replies between mutual follows about 4x the weight; others get a grey "not mutual" pill. ⭐ marks regulars (commented on 5+ days this month). A pill counts the last 30 days: "you owe N", "even" or "they owe you N". Once you reply on their post they drop off until they comment again.
- **Rising**: posts climbing fast on your topics, with topic chips and a "+ Topic" button.
- **Following** and **Followers**: the latest original posts from people you follow, or who follow you. People you keep replying to who never answer are marked one-way and moved down.
- **New builders**: real builders who just said hi on connect threads.
- **Watched**: accounts you pick (handles in the tab's ⚙), checked every 30 seconds, with a notification the minute they post. Runs in the background.
- **Trending**: terms and tools suddenly showing up across AI and founder posts, checked every 30 minutes, no pings. Runs in the background.
- **Cleanup**: people you follow who don't follow you back, in three groups: silent unfollowers (in an earlier follower snapshot, gone now), small accounts that never followed back, and big accounts (10k+) you probably follow on purpose. Each Fetch pulls both lists fresh (about 40 treg calls, a few cents) and saves a follower snapshot in `finder/data/follower-snapshots/`, so silent unfollowers are only caught from the second Fetch on. Read-only: never unfollow on the user's behalf.
- **Memes**: your meme library. Cmd+V to save an image, a GIF file or a GIF link (Giphy, Tenor), tag it, click a meme to copy it, then paste it into your reply. On a Mac, GIFs are copied as files so they paste as GIFs.

The ⚙ gear in each tab shows and edits its keywords and rules, with how many posts each rule removed. The 💬 counter shows how many replies the user posted today. Watched and Trending spend a little treg credit; the background button in the panel switches them off.

## Optional: SuperX (scheduling and analytics)

Not needed for the finder. Useful for scheduling posts and reading reply stats. If the user has SuperX:

```
claude mcp add --transport http superx https://api.superx.so/v1/mcp --header "Authorization: Bearer <SUPERX_API_KEY>"
```

(or `npm install -g superx-cli` then `superx login`). Key from https://app.superx.so/account?tab=api.

## Day to day

- When they say **"review my skips"**, follow `finder/docs/SKIP-REVIEW.md` and propose new filters.
- When they want to change keywords or rules, edit `finder/config.local.json` (or they can use the ⚙ gear in the panel).
- To re-tune thresholds for their niche, run `research/velocity-tracker/tracker.py` for an evening (about $1), then `calibrate.py`.

## Rules for you

- Never invent numbers in posts you help write. Use their real numbers.
- Don't post, follow, or DM on the user's behalf unless they explicitly ask.
- Keep their data local. `finder/data/` and `finder/config.local.json` are theirs and should never be committed or shared.
