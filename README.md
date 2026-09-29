# zero-to-1k

How I took a dead X account from **195 to ~700 followers in 4 days**, by reverse-engineering Rob Hallam's growth experiment. Free and open source.

By [@BertrandDiouly](https://x.com/BertrandDiouly).

## What's inside

| | |
|---|---|
| [`PLAYBOOK.md`](PLAYBOOK.md) | The step-by-step playbook: profile, day 1, day 2, posts, milestones, routine, what didn't work |
| [`finder/`](zero-to-1k) | The finder I built: shows X posts that are climbing fast enough to be worth a reply, with filters you can see and edit. Runs on your machine, plus a Chrome side-panel extension |
| [`lessons/`](lessons) | The bio lesson, and a prompt to have your agent write your bio |
| [`research/`](research) | Rob's run (post IDs + metrics), the velocity tracker, and my own numbers |

## The one idea

A reply borrows its reach from the post under it. Rob's replies under posts that ended below 2k views hit 100+ views 1% of the time; under posts that ended 10k to 100k, 24%. So the game is finding posts that are about to get big, early.

With the finder, my typical reply went from 13 views to 39, and replies with 100+ views went from 11 to 35 in a similar number of replies.

## Set it up

This is built for AI founders who use Claude Code, Codex or a similar agent. Open this folder in your agent and say:

> Set this up for me. Follow AGENTS.md.

You'll need a [treg.to](https://treg.to) account (pay per call, about 1 to 3 cents per Fetch). No servers, no keys handled by me: everything runs on your machine with your own account.

## Tell me how it goes

This is a beta. If you run it, send me your before and after, even if it didn't work. DM [@BertrandDiouly](https://x.com/BertrandDiouly).

License: MIT.
