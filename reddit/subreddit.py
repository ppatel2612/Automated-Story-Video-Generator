import json
import re
from pathlib import Path

from utils.console import print_step, print_substep

STORY_PATH = Path("data/story.json")


def _slug(value: str) -> str:
    """Make a simple id that is safe to use in paths and fake Reddit URLs."""
    slug = re.sub(r"[^\w\s-]", "", value).strip().lower()
    slug = re.sub(r"[\s_]+", "_", slug)
    return slug or "local_story"


def _normalise_comment(comment, index: int, thread_id: str) -> dict:
    """Accept either a plain string or a dict and return the old comment shape."""
    if isinstance(comment, str):
        body = comment
        comment_id = f"local_comment_{index}"
        comment_url = f"/r/local/comments/{thread_id}/local_story/{comment_id}/"
    else:
        body = comment.get("comment_body") or comment.get("body") or comment.get("text") or ""
        comment_id = comment.get("comment_id") or comment.get("id") or f"local_comment_{index}"
        comment_url = (
            comment.get("comment_url")
            or comment.get("permalink")
            or f"/r/local/comments/{thread_id}/local_story/{comment_id}/"
        )

    return {
        "comment_body": body,
        "comment_url": comment_url,
        "comment_id": comment_id,
    }


def _comment_has_text(comment) -> bool:
    """Skip empty comments so TTS and card rendering do not receive blanks."""
    if isinstance(comment, str):
        return bool(comment.strip())
    if not isinstance(comment, dict):
        return False
    body = comment.get("comment_body") or comment.get("body") or comment.get("text") or ""
    return bool(body.strip())


def get_subreddit_threads(POST_ID: str = None, story_path: str | Path = None):
    """
    Load a local story and return the same dict shape the rest of the app expects.

    POST_ID is kept in the signature so main.py can keep calling this function the
    same way it did when the project used the Reddit API.
    """

    story_path = Path(story_path) if story_path else STORY_PATH

    print_step(f"Loading local story from {story_path}...")

    if not story_path.exists():
        raise FileNotFoundError(
            f"Could not find {story_path}. Add a story JSON file before running the bot."
        )

    with story_path.open(encoding="utf-8") as story_file:
        story = json.load(story_file)

    thread_title = story.get("thread_title") or story.get("title") or "Local Reddit Story"
    thread_id = story.get("thread_id") or story.get("id") or _slug(thread_title)
    raw_comments = story.get("comments", [])

    content = {
        "thread_url": story.get("thread_url")
        or f"https://local.reddit.invalid/r/local/comments/{thread_id}/local_story/",
        "thread_title": thread_title,
        "thread_id": thread_id,
        "is_nsfw": story.get("is_nsfw", False),
        "comments": [
            _normalise_comment(comment, index, thread_id)
            for index, comment in enumerate(raw_comments)
            if _comment_has_text(comment)
        ],
    }

    if "thread_post" in story:
        content["thread_post"] = story["thread_post"]

    print_substep(f"Video will be: {content['thread_title']} :thumbsup:", style="bold green")
    print_substep(f"Thread url is: {content['thread_url']} :thumbsup:", style="bold green")
    print_substep(f"Loaded {len(content['comments'])} local comments", style="bold blue")
    print_substep("Received local story successfully.", style="bold green")
    return content
