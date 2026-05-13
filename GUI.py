import webbrowser
from io import BytesIO
import os
from pathlib import Path

# Used "tomlkit" instead of "toml" because it doesn't change formatting on "dump"
import tomlkit
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
    jsonify,
)

import utils.gui_utils as gui
from utils.text_style import (
    TEXT_STYLE_FIELDS,
    get_text_style,
    load_profiles,
    normalize_style,
    render_text_preview,
    save_profiles,
    style_from_form,
    update_config_text_style,
)
from utils.story_input import save_story_markdown, slug

# Set the hostname
HOST = "localhost"
# Set the port number
PORT = 4000

# Configure application
app = Flask(__name__, template_folder="GUI")

# Configure secret key only to use 'flash'
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Display index.html
@app.route("/")
def index():
    return render_template("index.html", file="videos.json")


@app.route("/backgrounds", methods=["GET"])
def backgrounds():
    return render_template("backgrounds.html", file="backgrounds.json")


@app.route("/background/add", methods=["POST"])
def background_add():
    # Get form values
    youtube_uri = request.form.get("youtube_uri").strip()
    filename = request.form.get("filename").strip()
    citation = request.form.get("citation").strip()
    position = request.form.get("position").strip()

    gui.add_background(youtube_uri, filename, citation, position)

    return redirect(url_for("backgrounds"))


@app.route("/background/delete", methods=["POST"])
def background_delete():
    key = request.form.get("background-key")
    gui.delete_background(key)

    return redirect(url_for("backgrounds"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    config_load = tomlkit.loads(Path("config.toml").read_text())
    config = gui.get_config(config_load)

    # Get checks for all values
    checks = gui.get_checks()

    if request.method == "POST":
        # Get data from form as dict
        data = request.form.to_dict()

        # Change settings
        config = gui.modify_settings(data, config_load, checks)

    return render_template("settings.html", file="config.toml", data=config, checks=checks)


@app.route("/text-style", methods=["GET", "POST"])
def text_style():
    config_load = tomlkit.loads(Path("config.toml").read_text())
    profiles = load_profiles()

    if request.method == "POST":
        action = request.form.get("action", "save_settings")
        profile_name = request.form.get("profile_name", "").strip()

        if action == "load_profile":
            if profile_name in profiles:
                update_config_text_style(profiles[profile_name])
                flash(f'Loaded text profile "{profile_name}".')
            else:
                flash("Choose a text profile to load.", "error")
            return redirect(url_for("text_style"))

        if action == "delete_profile":
            if profile_name in profiles:
                profiles.pop(profile_name)
                save_profiles(profiles)
                flash(f'Deleted text profile "{profile_name}".')
            else:
                flash("Choose a text profile to delete.", "error")
            return redirect(url_for("text_style"))

        style = style_from_form(request.form)
        update_config_text_style(style)

        if action == "save_profile":
            if not profile_name:
                flash("Enter a profile name before saving.", "error")
            else:
                profiles[profile_name] = style
                save_profiles(profiles)
                flash(f'Saved text settings and profile "{profile_name}".')
        else:
            flash("Text preview settings saved.")

        return redirect(url_for("text_style"))

    style = get_text_style(config_load)
    return render_template(
        "text_style.html",
        file="config.toml",
        data=style,
        fields=list(TEXT_STYLE_FIELDS.keys()),
        profiles=profiles,
    )


@app.route("/text-style/preview")
def text_style_preview():
    config_load = tomlkit.loads(Path("config.toml").read_text())
    current = get_text_style(config_load)
    overrides = {
        name: request.args.get(name)
        for name in TEXT_STYLE_FIELDS
        if request.args.get(name) is not None
    }
    style = normalize_style({**current, **overrides})
    image = render_text_preview(style, request.args.get("preview_text"))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")


@app.route("/story-input", methods=["GET", "POST"])
def story_input():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        story = request.form.get("story", "").strip()
        story_id = request.form.get("story_id", "").strip() or slug(title)
        subreddit = request.form.get("subreddit", "local").strip() or "local"
        split_updates = request.form.get("split_updates") == "true"
        nsfw = request.form.get("nsfw") == "true"
        max_chars_per_video = request.form.get("max_chars_per_video", "").strip()

        if not title or not story:
            flash("Title and story text are required.", "error")
            return render_template(
                "story_input.html",
                file="data/stories/inbox",
                data=request.form,
            )

        path = save_story_markdown(
            title=title,
            story=story,
            story_id=story_id,
            subreddit=subreddit,
            nsfw=nsfw,
            split_updates=split_updates,
            max_chars_per_video=int(max_chars_per_video) if max_chars_per_video else None,
        )
        flash(f"Saved story to {path}. Run the queue renderer to create the video.")
        return redirect(url_for("story_input"))

    return render_template("story_input.html", file="data/stories/inbox", data={})


def _api_token_is_valid() -> bool:
    expected_token = os.environ.get("STORY_API_TOKEN", "").strip()
    if not expected_token:
        return False
    auth_header = request.headers.get("Authorization", "")
    return auth_header == f"Bearer {expected_token}"


@app.route("/api/stories", methods=["POST"])
def api_stories():
    if not _api_token_is_valid():
        return jsonify({"error": "Unauthorized or STORY_API_TOKEN is not configured."}), 401

    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    story = str(data.get("story", "")).strip()
    if not title or not story:
        return jsonify({"error": "Both title and story are required."}), 400

    try:
        path = save_story_markdown(
            title=title,
            story=story,
            story_id=str(data.get("story_id", "")).strip(),
            subreddit=str(data.get("subreddit", "local")).strip() or "local",
            nsfw=bool(data.get("nsfw", False)),
            split_updates=bool(data.get("split_updates", True)),
            max_chars_per_video=(
                int(data["max_chars_per_video"]) if data.get("max_chars_per_video") else None
            ),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify(
        {
            "status": "saved",
            "path": str(path),
            "title": title,
            "render_command": "source venvDigger/bin/activate && python render_queue.py",
        }
    )


# Make videos.json accessible
@app.route("/videos.json")
def videos_json():
    return send_from_directory("video_creation/data", "videos.json")


# Make backgrounds.json accessible
@app.route("/backgrounds.json")
def backgrounds_json():
    return send_from_directory("utils", "backgrounds.json")


# Make videos in results folder accessible
@app.route("/results/<path:name>")
def results(name):
    return send_from_directory("results", name, as_attachment=True)


# Make voices samples in voices folder accessible
@app.route("/voices/<path:name>")
def voices(name):
    return send_from_directory("GUI/voices", name, as_attachment=True)


# Run browser and start the app
if __name__ == "__main__":
    webbrowser.open(f"http://{HOST}:{PORT}", new=2)
    print("Website opened in new tab. Refresh if it didn't load.")
    app.run(port=PORT)
