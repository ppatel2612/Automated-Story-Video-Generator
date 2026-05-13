from pathlib import Path

from utils.console import print_step, print_substep
from utils.story_input import load_story_file

STORY_PATH = Path("data/story.json")


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

    stories = load_story_file(story_path)
    content = stories[0]

    print_substep(f"Video will be: {content['thread_title']} :thumbsup:", style="bold green")
    print_substep(f"Thread url is: {content['thread_url']} :thumbsup:", style="bold green")
    print_substep(f"Loaded {len(content['comments'])} local comments", style="bold blue")
    print_substep("Received local story successfully.", style="bold green")
    return content
