# Video Queue

You can put legacy JSON files or new Markdown story files in this folder, then run:

```bash
source venvDigger/bin/activate
python render_queue.py
```

For pasted stories, prefer Markdown files in `data/stories/inbox`. Markdown preserves
quotes, triple quotes, and newlines without JSON escaping.

Successful story files move to `data/queue/done/`.
Failed story files move to `data/queue/failed/` with an `.error.txt` log.
Rendered videos are saved in the normal `results/<subreddit>/` folder.
