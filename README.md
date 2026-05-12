# Fully Automated Reddit Stories Video Generator & Poster to TikTok, Instagram Reels, and YouTube Shorts

> ⚠️ **Notice:** This project is no longer actively maintained. It remains fully functional, and pull requests are welcome.

## What this does
This repository generates Reddit story videos and optionally uploads them to:
- TikTok
- Instagram Reels
- YouTube Shorts

It includes:
- Reddit story scraping
- TTS voice generation
- background audio/video composition
- one-word caption overlays
- uploaders for TikTok, Instagram, and YouTube
- support for ElevenLabs API key rotation and StreamLabs Polly

## Requirements
- Linux is recommended.
- Python 3.10 or 3.12
- `ffmpeg` installed or available via script install
- `npm` / `node` for TikTok signature support
- `yt-dlp` for background video downloads (optional)

## Quick setup
1. Open a terminal in the repo root.
2. Create and activate the Python virtual environment:
   ```bash
   python3.12 -m venv venvDigger
   source venvDigger/bin/activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pydantic==2.7.4
   ```
4. Run the bot once to create `config.toml`:
   ```bash
   python3 main.py
   ```
   - If `config.toml` does not exist, `main.py` builds it from `utils/.config.template.toml`.
   - Use the CLI or edit `config.toml` manually.

## Full install and setup

### 1. Configure the bot
- Open `config.toml` in the repo root.
- Required settings:
  - `reddit` credentials and app details
  - `reddit.thread.subreddit` or `reddit.thread.post_id`
  - `settings.tts.voice_choice`
  - `settings.tts.elevenlabs_api_key` if using ElevenLabs
  - `settings.tts.tiktok_sessionid` if using `voice_choice = "tiktok"`

> Note: `main.py` exits if `voice_choice` is `tiktok` and `tiktok_sessionid` is missing.

### 2. Background video and audio
Download a background video and save it as:
- `assets/backgrounds/video/bbswitzer-parkour.mp4`

Example command:
```bash
yt-dlp -f 'bestvideo[height=1080]+bestaudio/best' -ciw -o '%(title)s.%(ext)s' <video_url>
```

### 3. ElevenLabs key rotation
If using ElevenLabs, add API keys to `elevenLabsKeyRotator.py`.
- The script rotates keys before the main run.
- Use enough keys for your upload cadence.

If you do not want ElevenLabs, disable or skip `elevenLabsKeyRotator.py` in `Automator.sh`.

### 4. TikTok uploader setup
From the repo root:
```bash
cd uploaders/TiktokAutoUploader
python3.12 -m venv .tokvenv
source .tokvenv/bin/activate
pip install -r requirements.txt
cd tiktok_uploader/tiktok-signature/
npm install
npx playwright install
```

Login with:
```bash
source .tokvenv/bin/activate
python3 cli.py login -n <your_tiktok_username>
```
Copy the `CookiesDir` to your server if you log in from another machine.

### 5. Instagram uploader setup
- Edit `uploaders/instagram_creds.conf` with your Instagram credentials.
- Test upload:
  ```bash
  python3 uploaders/instaUpload.py "path_to_video" "description"
  ```

Notes:
- Instagram login may require SMS or re-entering your password.
- 2FA is not supported by this script.

### 6. YouTube uploader setup
- Create a YouTube API v3 client in Google Cloud Console.
- Place `youtube_client_secret.json` in `uploaders/`.
- Test upload:
  ```bash
  python3 uploaders/youtubeUpload.py "path_to_video" "description"
  ```
- The first run opens a browser and creates `YTtoken.json`.

### 7. Caption generation
Use `captionGen.py` to add word-by-word captions after your video is generated.
- If you need less RAM, edit `captionGen.py` to use `vosk-model-small-en-us-0.15`.

## Running the program

### Generate a video only
Activate the bot environment and run:
```bash
source venvDigger/bin/activate
python3 main.py
```

### Run the full automated flow
```bash
./RunFullFlowInstant.sh
```

### Run the automator script
`Automator.sh` covers the full chain:
- random sleep
- activate venv
- run `elevenLabsKeyRotator.py`
- run `main.py`
- generate captions via `captionGen.py`
- upload to YouTube, Instagram, and TikTok

To run manually:
```bash
./Automator.sh
```

### Schedule with cron
Example:
```bash
0 */7 * * * su user -c '/home/user/RedditVideoMakerBot-master/Automator.sh'
```

## Troubleshooting
- If `main.py` fails, check `config.toml` for missing Reddit or TTS settings.
- If TikTok voice is enabled, ensure `settings.tts.tiktok_sessionid` exists.
- If uploader scripts fail, verify credentials and tokens for each platform.

## Notes
- Linux / WSL is the recommended platform.
- Updating subreddits may require adjusting paths in `Automator.sh`.
- Keep credentials, API keys, and token files secure.

## Project status
This repo is not actively maintained, but it is functional. Pull requests are welcome.
