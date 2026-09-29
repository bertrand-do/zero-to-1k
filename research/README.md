# Research

The data behind every rule in the finder and the playbook. Point your agent here if you want to run your own experiment or check my numbers.

## rob-experiment/

Rob Hallam's public growth experiment on the @robmailserver account (22 to 25 September 2026). He later revealed on @robj3d3 that the persona was fake, and he said publicly that follow-for-follow was part of it. Keep that in mind.

| File | What |
|---|---|
| `rob-posts.csv` | All 638 posts on the account (originals, quotes, replies, reposts) with IDs, dates and metrics. Metrics are cumulative snapshots from 25 Sep 2026. |
| `rob-replies-days-1-2.csv` | His 264 replies on days 1 and 2, joined with the post he replied to: the author's follower count, how old the post was when he replied, and how many views it ended with. This is the table the framework is built on. |
| `refetch.py` | Downloads the full text of every post above with your own treg key (≈ $0.90). |

**Why only IDs?** X lets you share post IDs, not copies of other people's posts. The analysis is ours, so it's all here. The text you re-download yourself.

## velocity-tracker/

90 fresh AI posts checked every 30 minutes for about 8 hours (25 Sep 2026 evening). It answers: if a post has N views at 30 or 60 minutes, how often does it reach 10k? Results are in `finder/docs/FRAMEWORK.md`. `tracker.py` and `calibrate.py` let you run your own (≈ $1 per run) and re-tune the thresholds for your niche.

## my-run.md

My own numbers from the first days, so you have a baseline to compare against.

## What the data can't tell you

- How many views a post had at the exact moment Rob replied. We only have final counts; the velocity tracker is the stand-in.
- Why any single follow happened. Replies, profile visits and follow-backs mix together.
- One evening of tracking is a small sample. Re-run it in your niche.
