# Turning skips into filters

Every time you press **Skip** on a card and give a reason, it's saved to `finder/data/feedback.jsonl` with the post's author, text and stats.

After a session, ask your agent: **"review my skips"**. It should:

1. Read `data/feedback.jsonl` and group the skips by reason.
2. For each group, look at what the skipped posts have in common: a word in the text, a pattern in the handle or name, account size, reply count vs likes.
3. Propose the smallest rule that catches that pattern, and test it against the posts you did NOT skip so it doesn't remove good ones.
4. Apply it: a new keyword or blocklist pattern in `config.local.json`, or a small rule in `app/rising.py`.
5. Fetch again and check the Filters page: the new rule should show "N out".

Real examples from my run:
- "off-topic": the keyword `grok` pulled in "@grok is this true?" posts → new rule: drop posts that summon @grok, and search `grokbot` instead.
- "off-topic": `muse` pulled in a hockey reporter called Dan Muse → search `muse (meta OR ai OR app OR assistant OR zuck)`.
- "crypto / finance": handles like `0x…`, `…defi`, `bitcoin…` → crypto name blocklist.
- "bot / spam": posts with 3+ hashtags or long emoji chains → spam rule.
