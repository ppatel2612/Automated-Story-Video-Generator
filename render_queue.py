#!/usr/bin/env python
import math
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

from reddit.subreddit import get_subreddit_threads
from utils import settings
from utils.console import print_step, print_substep
from utils.ffmpeg_install import ffmpeg_install
from utils.id import id
from video_creation.background import (
    chop_background,
    download_background_audio,
    download_background_video,
    get_background_config,
)
from video_creation.final_video import make_final_video
from video_creation.screenshot_downloader import get_screenshots_of_reddit_posts
from video_creation.voices import save_text_to_mp3

QUEUE_DIR = Path("data/queue")
DONE_DIR = QUEUE_DIR / "done"
FAILED_DIR = QUEUE_DIR / "failed"


def _prepare_queue_dirs() -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)


def _queued_stories() -> list[Path]:
    _prepare_queue_dirs()
    return sorted(path for path in QUEUE_DIR.glob("*.json") if path.is_file())


def _unique_destination(directory: Path, filename: str) -> Path:
    destination = directory / filename
    if not destination.exists():
        return destination

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return directory / f"{Path(filename).stem}-{stamp}{Path(filename).suffix}"


def _move_story(story_path: Path, directory: Path) -> Path:
    destination = _unique_destination(directory, story_path.name)
    shutil.move(str(story_path), destination)
    return destination


def _render_story(story_path: Path) -> None:
    reddit_object = get_subreddit_threads(story_path=story_path)
    reddit_id = id(reddit_object)
    length, number_of_comments = save_text_to_mp3(reddit_object)
    length = math.ceil(length)
    get_screenshots_of_reddit_posts(reddit_object, number_of_comments)
    bg_config = {
        "video": get_background_config("video"),
        "audio": get_background_config("audio"),
    }
    download_background_video(bg_config["video"])
    download_background_audio(bg_config["audio"])
    chop_background(bg_config, length, reddit_object)
    make_final_video(number_of_comments, length, reddit_object, bg_config)


def _record_failed_story(story_path: Path) -> None:
    failed_path = _move_story(story_path, FAILED_DIR)
    error_path = failed_path.with_suffix(failed_path.suffix + ".error.txt")
    error_path.write_text(traceback.format_exc(), encoding="utf-8")
    print_substep(
        f"Failed: moved {story_path.name} to {failed_path} and saved the error log.",
        style="bold red",
    )


def _load_config() -> dict:
    directory = Path().absolute()
    config = settings.check_toml(
        f"{directory}/utils/.config.template.toml", f"{directory}/config.toml"
    )
    if config is False:
        sys.exit(1)

    if (
        not settings.config["settings"]["tts"]["tiktok_sessionid"]
        or settings.config["settings"]["tts"]["tiktok_sessionid"] == ""
    ) and config["settings"]["tts"]["voice_choice"] == "tiktok":
        print_substep(
            "TikTok voice requires a sessionid! Check the documentation on how to obtain one.",
            "bold red",
        )
        sys.exit(1)

    return config


def main() -> int:
    ffmpeg_install()
    _load_config()

    stories = _queued_stories()
    if not stories:
        print_step("No queued stories found.")
        print_substep("Add one JSON file per story to data/queue, then run this script again.")
        return 0

    print_step(f"Found {len(stories)} queued stor{'y' if len(stories) == 1 else 'ies'}.")
    successes = 0
    failures = 0

    for index, story_path in enumerate(stories, start=1):
        print_step(f"Rendering queued story {index} of {len(stories)}: {story_path.name}")
        try:
            _render_story(story_path)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            failures += 1
            _record_failed_story(story_path)
            continue
        except Exception:
            failures += 1
            _record_failed_story(story_path)
            continue

        successes += 1
        done_path = _move_story(story_path, DONE_DIR)
        print_substep(f"Completed: moved {story_path.name} to {done_path}", style="bold green")

    print_step(f"Queue complete. Successful: {successes}. Failed: {failures}.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
