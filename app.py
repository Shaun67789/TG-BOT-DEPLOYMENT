import os
import subprocess
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from bot_manager import start_bot, stop_bot, status, get_logs
from utils import safe_extract_zip

# ================= CONFIG =================

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BOTS_DIR = os.path.join(BASE_DIR, "Bots")

os.makedirs(BOTS_DIR, exist_ok=True)

# ================= HELPERS =================

def get_bot_path(name):
    return os.path.join(BOTS_DIR, name)

def get_main_file(name):
    path = os.path.join(get_bot_path(name), "main.txt")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

# ================= ROUTES =================

@app.route("/")
def index():
    bots = []
    for bot in os.listdir(BOTS_DIR):
        bot_path = get_bot_path(bot)
        if os.path.isdir(bot_path):
            bots.append({
                "name": bot,
                "status": status(bot)
            })
    return render_template("index.html", bots=bots)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        zip_file = request.files.get("zip")
        main_file = request.form.get("main")

        if not zip_file or not main_file:
            flash("ZIP file and main file name are required")
            return redirect(url_for("upload"))

        if not zip_file.filename.endswith(".zip"):
            flash("Only ZIP files are allowed")
            return redirect(url_for("upload"))

        bot_name = os.path.splitext(zip_file.filename)[0]
        bot_path = get_bot_path(bot_name)

        os.makedirs(bot_path, exist_ok=True)

        zip_path = os.path.join(bot_path, zip_file.filename)
        zip_file.save(zip_path)

        try:
            safe_extract_zip(zip_path, bot_path)
        except Exception as e:
            flash("Failed to extract ZIP")
            return redirect(url_for("upload"))
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

        # Save main file name
        with open(os.path.join(bot_path, "main.txt"), "w", encoding="utf-8") as f:
            f.write(main_file.strip())

        # Install dependencies safely
        req_path = os.path.join(bot_path, "requirements.txt")
        if os.path.exists(req_path):
            subprocess.call(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=bot_path
            )

        flash("Bot uploaded successfully")
        return redirect(url_for("index"))

    return render_template("upload.html")


@app.route("/bot/<name>")
def bot_page(name):
    bot_path = get_bot_path(name)
    if not os.path.isdir(bot_path):
        abort(404)

    return render_template(
        "bot.html",
        name=name,
        status=status(name)
    )


@app.route("/start/<name>")
def start(name):
    bot_path = get_bot_path(name)
    if not os.path.isdir(bot_path):
        abort(404)

    main_file = get_main_file(name)
    if not main_file:
        flash("Main file not configured")
        return redirect(url_for("bot_page", name=name))

    start_bot(name, main_file)
    return redirect(url_for("bot_page", name=name))


@app.route("/stop/<name>")
def stop(name):
    bot_path = get_bot_path(name)
    if not os.path.isdir(bot_path):
        abort(404)

    stop_bot(name)
    return redirect(url_for("bot_page", name=name))


@app.route("/logs/<name>")
def logs(name):
    bot_path = get_bot_path(name)
    if not os.path.isdir(bot_path):
        abort(404)

    return render_template(
        "logs.html",
        name=name,
        logs=get_logs(name)
    )


# ===== AJAX RAW LOGS (used by app.js) =====

@app.route("/logs_raw/<name>")
def logs_raw(name):
    bot_path = get_bot_path(name)
    if not os.path.isdir(bot_path):
        abort(404)

    return get_logs(name)


# ================= ENTRY =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
