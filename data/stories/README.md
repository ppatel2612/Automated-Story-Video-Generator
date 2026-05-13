# Markdown Story Input

Put Markdown stories in `data/stories/inbox`, then run:

```bash
source venvDigger/bin/activate
python render_queue.py
```

Markdown is safer than hand-written JSON for stories because quotes, triple quotes,
apostrophes, and newlines can be pasted directly into the body.

Use front matter for metadata:

```markdown
---
id: my_story_id
title: My Story Title
subreddit: local
nsfw: false
split_updates: true
max_chars_per_video: 1000
---

Paste the story here.

Quotes like "this" and triple quotes like """this""" are fine.

## Update 1

If `split_updates` is true, this update becomes a separate video.
```

If a section is still longer than `max_chars_per_video`, it is split into
`Part 1`, `Part 2`, etc. before TTS and video rendering. This keeps very long
stories from becoming one oversized render.

Successful files move to `data/stories/done`.
Failed files move to `data/stories/failed` with an `.error.txt` log.
