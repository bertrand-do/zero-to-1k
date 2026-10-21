# zero-to-1k

A free, open source reply finder for X that runs on your own computer. I built it while growing my account [@BertrandDiouly](https://x.com/BertrandDiouly) from **195 followers to 1,212 in 26 days** (25 September to 20 October 2026).

With the finder, my typical reply went from 13 views to 39, and replies with 100+ views went from 11 to 35 in a similar number of replies. And of the 446 times I paid someone back on the Mutuals tab, 58% of those people came back to my posts within 3 days.

## What it does

The finder lives in a side panel next to X, with one tab per job:

- **Mutuals**: the people who commented on your posts or answered your replies in the last 48 hours, so you can pay them back with a reply. It also counts who you owe and who owes you, and puts real mutuals (you follow each other) first, because X's ranking code gives their replies about 4x the weight.
- **Rising**: posts on your topics that are climbing fast right now, so your reply lands early under a post that is about to get big.
- **Following / Followers**: the latest posts from the people you follow and the people who follow you.
- **New builders**: real builders who just said hi on connect threads.
- **Watched**: a ping the minute an account you pick posts.
- **Trending**: terms and tools that suddenly show up across AI and founder posts.
- **Cleanup**: people you follow who don't follow you back, with silent unfollowers first (they followed you before and quietly left). It never unfollows for you: you open their profile and decide.
- **Memes**: your own meme library. Paste an image or a GIF link, tag it, and click to copy it into a reply.

## Get started in 3 steps

You need Claude Code, Codex or a similar coding agent, and Chrome (or another Chromium browser like Brave, Arc or Comet).

### 1. Paste this into your agent

```
Clone https://github.com/bertrand-do/zero-to-1k and set it up for me. Follow AGENTS.md.
```

It works from any folder. Your agent downloads the repo, installs what it needs and walks you through the rest one step at a time.

### 2. Load the extension in Chrome

Your agent will tell you the exact folder to pick. Then:

1. Open a new tab and go to `chrome://extensions`.
2. Turn on **Developer mode** with the toggle in the top right corner.
3. Click **Load unpacked**.
4. Pick the `finder/extension` folder inside the repo.
5. Click the puzzle piece icon in the Chrome toolbar and pin **Zero to 1k**, so the icon stays visible.

Open x.com and click the icon. The panel opens next to X.

### 3. Connect treg.to

The finder gets its X data from [treg.to](https://treg.to), which you pay per call from a prepaid balance. A Fetch costs about 1 to 3 cents. Your agent installs treg and logs you in.

If you don't have a treg account yet, you can sign up with my referral link: https://treg.to/?ref=bdiouly-5h5gs. You get a $5 bonus when you add $10 (I get a small referral credit too).

Then press **Fetch** on the **Mutuals** tab. That's it.

## The one idea

A reply borrows its reach from the post under it. In Rob Hallam's growth experiment, his replies under posts that ended below 2k views reached 100+ views 1% of the time. Under posts that ended between 10k and 100k views, it was 24%. So the game is finding the posts that are about to get big, early, and paying back the people who already show up for you.

## What else is in here

| | |
|---|---|
| [`PLAYBOOK.md`](PLAYBOOK.md) | How the first 4 days went: profile, day 1, day 2, posts, milestones, routine, what didn't work |
| [`finder/`](finder) | The finder and the Chrome side panel extension. Everything runs on your machine with your own treg account |
| [`lessons/`](lessons) | The bio lesson, and a prompt to have your agent write your bio |
| [`research/`](research) | Rob's run (post IDs and metrics), the velocity tracker, and my own numbers |

## Tell me how it goes

This is a beta. If you run it, send me your before and after, even if it didn't work. DM [@BertrandDiouly](https://x.com/BertrandDiouly).

License: MIT.
