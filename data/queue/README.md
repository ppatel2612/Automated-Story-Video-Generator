# Video Queue

Put one local story JSON file per video in this folder, then run:

```bash
source venvDigger/bin/activate
python render_queue.py
```

Successful story files move to `data/queue/done/`.
Failed story files move to `data/queue/failed/` with an `.error.txt` log.
Rendered videos are saved in the normal `results/<subreddit>/` folder.
