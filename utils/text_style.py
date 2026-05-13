import json
from pathlib import Path
from typing import Any

import tomlkit
from PIL import Image, ImageDraw, ImageFont


PROFILE_PATH = Path("data/text_style_profiles.json")

TEXT_STYLE_DEFAULTS: dict[str, Any] = {
    "font_size": 100,
    "title_font_size": 38,
    "body_font_size": 31,
    "meta_font_size": 23,
    "font_color": "255,255,255",
    "muted_color": "215,215,215",
    "background_color": "0,0,0",
    "background_opacity": 0.0,
    "outline_color": "0,0,0",
    "outline_size": 4,
    "line_padding": 5,
    "wrap_width": 30,
    "card_width": 900,
    "card_padding": 44,
    "border_radius": 28,
    "overlay_width_percent": 88,
    "segment_max_chars": 75,
    "segment_max_words": 5,
}

TEXT_STYLE_FIELDS: dict[str, dict[str, Any]] = {
    "font_size": {"type": int, "min": 12, "max": 260},
    "title_font_size": {"type": int, "min": 12, "max": 180},
    "body_font_size": {"type": int, "min": 12, "max": 180},
    "meta_font_size": {"type": int, "min": 8, "max": 120},
    "font_color": {"type": "color"},
    "muted_color": {"type": "color"},
    "background_color": {"type": "color"},
    "background_opacity": {"type": float, "min": 0, "max": 1},
    "outline_color": {"type": "color"},
    "outline_size": {"type": int, "min": 0, "max": 30},
    "line_padding": {"type": int, "min": 0, "max": 80},
    "wrap_width": {"type": int, "min": 8, "max": 100},
    "card_width": {"type": int, "min": 300, "max": 1600},
    "card_padding": {"type": int, "min": 0, "max": 180},
    "border_radius": {"type": int, "min": 0, "max": 120},
    "overlay_width_percent": {"type": int, "min": 35, "max": 100},
    "segment_max_chars": {"type": int, "min": 25, "max": 180},
    "segment_max_words": {"type": int, "min": 1, "max": 30},
}


def parse_color(value: Any, default: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int, int]:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        parts = value[:3]
    else:
        parts = str(value).replace("#", "").split(",")
        if len(parts) == 1 and len(parts[0]) == 6:
            try:
                return tuple(int(parts[0][i : i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                return default
    try:
        rgb = tuple(max(0, min(255, int(part))) for part in parts)
    except (TypeError, ValueError):
        return default
    return rgb if len(rgb) == 3 else default


def color_string(value: Any, default: str = "255,255,255") -> str:
    return ",".join(str(part) for part in parse_color(value, parse_color(default)))


def _coerce_field(name: str, value: Any) -> Any:
    rules = TEXT_STYLE_FIELDS[name]
    if rules["type"] == "color":
        return color_string(value, TEXT_STYLE_DEFAULTS[name])

    coerced = rules["type"](value)
    if "min" in rules:
        coerced = max(rules["min"], coerced)
    if "max" in rules:
        coerced = min(rules["max"], coerced)
    return coerced


def normalize_style(values: dict[str, Any] | None = None) -> dict[str, Any]:
    style = TEXT_STYLE_DEFAULTS.copy()
    if values:
        style.update({key: values[key] for key in values if key in TEXT_STYLE_FIELDS})

    normalized = {}
    for name in TEXT_STYLE_FIELDS:
        try:
            normalized[name] = _coerce_field(name, style[name])
        except (TypeError, ValueError):
            normalized[name] = TEXT_STYLE_DEFAULTS[name]
    return normalized


def get_text_style(config: dict | None = None) -> dict[str, Any]:
    settings = config.get("settings", {}) if isinstance(config, dict) else {}
    return normalize_style(settings.get("text", {}))


def style_from_form(form: dict[str, Any]) -> dict[str, Any]:
    return normalize_style({name: form.get(name) for name in TEXT_STYLE_FIELDS})


def update_config_text_style(style: dict[str, Any], config_path: str = "config.toml") -> None:
    config_file = Path(config_path)
    config = tomlkit.loads(config_file.read_text()) if config_file.exists() else tomlkit.document()
    if "settings" not in config:
        config["settings"] = tomlkit.table()
    config["settings"]["text"] = normalize_style(style)
    config_file.write_text(tomlkit.dumps(config))


def load_profiles() -> dict[str, dict[str, Any]]:
    if not PROFILE_PATH.exists():
        return {}
    try:
        data = json.loads(PROFILE_PATH.read_text())
    except json.JSONDecodeError:
        return {}
    return {name: normalize_style(style) for name, style in data.items() if isinstance(style, dict)}


def save_profiles(profiles: dict[str, dict[str, Any]]) -> None:
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(profiles, indent=4, sort_keys=True))


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = ["Roboto-Black.ttf", "Roboto-Bold.ttf", "Rubik-Black.ttf"] if bold else [
        "Roboto-Regular.ttf",
        "Roboto-Bold.ttf",
    ]
    for name in names:
        path = Path("fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def draw_centered_text(
    image: Image.Image,
    text: str,
    style: dict[str, Any],
    *,
    transparent: bool = False,
) -> None:
    draw = ImageDraw.Draw(image)
    font = _load_font(style["font_size"], bold=transparent)
    lines = []
    words = text.split()
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= style["wrap_width"]:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if not lines:
        lines = [text]

    text_color = parse_color(style["font_color"])
    outline_color = parse_color(style["outline_color"], (0, 0, 0))
    outline_size = style["outline_size"]
    line_padding = style["line_padding"]
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = font.getbbox(line)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    block_height = sum(line_heights) + (line_padding * (len(lines) - 1))
    y = (image.height - block_height) / 2
    for index, line in enumerate(lines):
        x = (image.width - line_widths[index]) / 2
        if outline_size:
            for dx in range(-outline_size, outline_size + 1):
                for dy in range(-outline_size, outline_size + 1):
                    if dx * dx + dy * dy <= outline_size * outline_size:
                        draw.text((x + dx, y + dy), line, font=font, fill=outline_color)
        draw.text((x, y), line, font=font, fill=text_color)
        y += line_heights[index] + line_padding


def render_text_preview(style: dict[str, Any], text: str | None = None) -> Image.Image:
    style = normalize_style(style)
    size = (960, 540)
    bg_alpha = round(style["background_opacity"] * 255)
    bg = (*parse_color(style["background_color"], (0, 0, 0)), bg_alpha)
    image = Image.new("RGBA", size, bg)
    draw_centered_text(
        image,
        text or "This is how your story text will look before rendering.",
        style,
        transparent=bg_alpha == 0,
    )
    return image
