# GPT Action Setup

This project exposes a small authenticated API endpoint that a Custom GPT can call
to save generated stories into `data/stories/inbox`.

## 1. Start The GUI/API Server

Choose a secret token. Do not commit or share it.

```bash
export STORY_API_TOKEN="replace-with-a-long-random-secret"
source venvDigger/bin/activate
python GUI.py
```

The endpoint is:

```text
POST /api/stories
```

## 2. Expose The Server To ChatGPT

ChatGPT cannot call `localhost` or `127.0.0.1` on your machine directly.
Use one of these:

- Cloudflare Tunnel
- ngrok
- a VPS or hosted deployment

You need a public HTTPS URL such as:

```text
https://your-domain.example.com
```

## 3. Configure The Custom GPT Action

1. Open your Custom GPT in the GPT Builder.
2. Go to **Configure**.
3. Add or edit **Actions**.
4. Use **API Key** or bearer-token authentication.
5. Paste the token from `STORY_API_TOKEN`.
6. Paste the schema from `docs/gpt_action_openapi.yaml`.
7. Replace `https://YOUR-PUBLIC-HTTPS-URL-HERE` with your public HTTPS URL.
8. Test the `saveStoryToVideoQueue` action.

## 4. Suggested GPT Instructions

Add this to your Custom GPT instructions:

```text
When the user approves a final story, call saveStoryToVideoQueue.
Send the full story text exactly as written, preserving paragraphs, quotes, and update headings.
Use headings like ## Update 1 and ## Update 2 for updates.
Set split_updates to true unless the user asks for one single video.
Do not escape quotes or newlines manually.
After saving, tell the user the story has been queued for rendering.
```

## 5. Render Queued Stories

After the GPT saves one or more stories:

```bash
source venvDigger/bin/activate
python render_queue.py
```

Successful Markdown files move from `data/stories/inbox` to `data/stories/done`.
Failed files move to `data/stories/failed`.

## Test With Curl

```bash
curl -X POST http://127.0.0.1:4000/api/stories \
  -H "Authorization: Bearer replace-with-a-long-random-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Story",
    "story": "This is a pasted story.\n\n## Update 1\n\nThis becomes a second video.",
    "subreddit": "local",
    "nsfw": false,
    "split_updates": true,
    "max_chars_per_video": 2000
  }'
```
