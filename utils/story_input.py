import json
import re
from pathlib import Path
from typing import Any


DEFAULT_THREAD_URL = "https://local.reddit.invalid/r/local/comments/{thread_id}/local_story/"
STORY_INBOX_DIR = Path("data/stories/inbox")
STORY_DONE_DIR = Path("data/stories/done")
STORY_FAILED_DIR = Path("data/stories/failed")


def slug(value: str) -> str:
    slug_value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    slug_value = re.sub(r"[\s_]+", "_", slug_value)
    return slug_value or "local_story"


def unique_story_path(title: str, directory: Path = STORY_INBOX_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    base_name = slug(title)
    path = directory / f"{base_name}.md"
    counter = 2
    while path.exists():
        path = directory / f"{base_name}_{counter}.md"
        counter += 1
    return path


def build_story_markdown(
    *,
    title: str,
    story: str,
    story_id: str = "",
    subreddit: str = "local",
    nsfw: bool = False,
    split_updates: bool = True,
    max_chars_per_video: int | None = None,
) -> str:
    front_matter = [
        "---",
        f"id: {story_id or slug(title)}",
        f"title: {title}",
        f"subreddit: {subreddit or 'local'}",
        f"nsfw: {str(bool(nsfw)).lower()}",
        f"split_updates: {str(bool(split_updates)).lower()}",
    ]
    if max_chars_per_video:
        front_matter.append(f"max_chars_per_video: {int(max_chars_per_video)}")
    return "\n".join(front_matter + ["---", "", story.strip(), ""])


def save_story_markdown(
    *,
    title: str,
    story: str,
    story_id: str = "",
    subreddit: str = "local",
    nsfw: bool = False,
    split_updates: bool = True,
    max_chars_per_video: int | None = None,
    directory: Path = STORY_INBOX_DIR,
) -> Path:
    if not title.strip():
        raise ValueError("Story title is required.")
    if not story.strip():
        raise ValueError("Story text is required.")

    path = unique_story_path(title, directory=directory)
    path.write_text(
        build_story_markdown(
            title=title.strip(),
            story=story,
            story_id=story_id.strip() if story_id else "",
            subreddit=subreddit.strip() if subreddit else "local",
            nsfw=nsfw,
            split_updates=split_updates,
            max_chars_per_video=max_chars_per_video,
        ),
        encoding="utf-8",
    )
    return path


def normalise_comment(comment: Any, index: int, thread_id: str) -> dict:
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


def comment_has_text(comment: Any) -> bool:
    if isinstance(comment, str):
        return bool(comment.strip())
    if not isinstance(comment, dict):
        return False
    body = comment.get("comment_body") or comment.get("body") or comment.get("text") or ""
    return bool(body.strip())


def normalise_story(story: dict, suffix: str = "") -> dict:
    thread_title = story.get("thread_title") or story.get("title") or "Local Reddit Story"
    thread_id = story.get("thread_id") or story.get("id") or slug(thread_title)
    if suffix:
        thread_id = f"{thread_id}_{suffix}"

    raw_comments = story.get("comments", [])
    content = {
        "thread_url": story.get("thread_url")
        or DEFAULT_THREAD_URL.format(thread_id=thread_id),
        "thread_title": thread_title,
        "thread_id": thread_id,
        "subreddit": story.get("subreddit", "local"),
        "is_nsfw": bool(story.get("is_nsfw", story.get("nsfw", False))),
        "comments": [
            normalise_comment(comment, index, thread_id)
            for index, comment in enumerate(raw_comments)
            if comment_has_text(comment)
        ],
    }

    if "thread_post" in story:
        content["thread_post"] = story["thread_post"]
    elif "body" in story:
        content["thread_post"] = story["body"]

    return content


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.casefold() in {"true", "yes"}:
        return True
    if value.casefold() in {"false", "no"}:
        return False
    if value.casefold() in {"null", "none"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_front_matter(markdown: str) -> tuple[dict, str]:
    if not markdown.startswith("---"):
        return {}, markdown

    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, markdown

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, markdown

    metadata = {}
    for line in lines[1:end_index]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = _parse_scalar(value)

    body = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, body


def _split_updates(body: str) -> list[tuple[str | None, str]]:
    update_heading = re.compile(r"^##+\s*(update\b.*)$", re.IGNORECASE | re.MULTILINE)
    matches = list(update_heading.finditer(body))
    if not matches:
        return [(None, body.strip())] if body.strip() else []

    sections = []
    intro = body[: matches[0].start()].strip()
    if intro:
        sections.append((None, intro))

    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        heading = match.group(1).strip()
        text = body[match.end() : next_start].strip()
        if text:
            sections.append((heading, text))
    return sections


def _split_text_by_length(text: str, max_chars: int) -> list[str]:
    text = text.strip()
    if max_chars <= 0 or len(text) <= max_chars:
        return [text] if text else []

    paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", paragraph) if sentence.strip()]
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(sentence) <= max_chars:
                    current = sentence
                else:
                    wrapped = [
                        part.strip()
                        for part in re.findall(r".{1,%d}(?:\s+|$)" % max_chars, sentence)
                        if part.strip()
                    ]
                    chunks.extend(wrapped[:-1])
                    current = wrapped[-1] if wrapped else ""

    if current:
        chunks.append(current)
    return chunks


def _story_from_markdown_section(
    metadata: dict,
    section_title: str | None,
    body: str,
    index: int,
    chunk_index: int = 0,
    chunk_count: int = 1,
) -> dict:
    base_title = metadata.get("thread_title") or metadata.get("title") or "Local Reddit Story"
    base_id = metadata.get("thread_id") or metadata.get("id") or slug(base_title)
    title = base_title if section_title is None else f"{base_title} - {section_title}"
    if chunk_count > 1:
        title = f"{title} - Part {chunk_index + 1}"
    suffix_parts = []
    if index != 0:
        suffix_parts.append(f"part_{index + 1}")
    if chunk_count > 1:
        suffix_parts.append(f"chunk_{chunk_index + 1}")
    suffix = "_".join(suffix_parts)
    thread_id = base_id if not suffix else f"{base_id}_{suffix}"

    return normalise_story(
        {
            "thread_id": thread_id,
            "thread_title": title,
            "thread_url": metadata.get("thread_url"),
            "subreddit": metadata.get("subreddit", "local"),
            "is_nsfw": metadata.get("is_nsfw", metadata.get("nsfw", False)),
            "thread_post": body,
            "comments": [],
        }
    )


def load_markdown_stories(path: str | Path, default_max_chars_per_video: int = 0) -> list[dict]:
    markdown = Path(path).read_text(encoding="utf-8")
    metadata, body = _parse_front_matter(markdown)
    split_updates = bool(metadata.get("split_updates", False))
    max_chars_per_video = int(
        metadata.get("max_chars_per_video")
        or metadata.get("storymode_max_length")
        or default_max_chars_per_video
        or 0
    )
    sections = _split_updates(body) if split_updates else [(None, body.strip())]

    stories = []
    for index, (section_title, section_body) in enumerate(sections):
        if not section_body.strip():
            continue
        chunks = _split_text_by_length(section_body, max_chars_per_video)
        for chunk_index, chunk in enumerate(chunks):
            stories.append(
                _story_from_markdown_section(
                    metadata,
                    section_title,
                    chunk,
                    index,
                    chunk_index=chunk_index,
                    chunk_count=len(chunks),
                )
            )
    if not stories:
        raise ValueError(f"No story body found in {path}.")
    return stories


def load_json_stories(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as story_file:
        story = json.load(story_file)

    if isinstance(story, list):
        return [normalise_story(item, suffix=f"part_{index + 1}") for index, item in enumerate(story)]
    return [normalise_story(story)]


def load_story_file(path: str | Path, default_max_chars_per_video: int = 0) -> list[dict]:
    path = Path(path)
    if path.suffix.casefold() == ".md":
        return load_markdown_stories(
            path,
            default_max_chars_per_video=default_max_chars_per_video,
        )
    if path.suffix.casefold() == ".json":
        return load_json_stories(path)
    raise ValueError(f"Unsupported story file type: {path.suffix}")
