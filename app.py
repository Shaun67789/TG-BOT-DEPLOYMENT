import os
import subprocess
import threading
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, abort, jsonify
)
from bot_manager import start_bot, stop_bot, status, get_logs
from utils import safe_extract_zip, install_requirements_async

# ================= CONFIG =================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-key")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BOTS_DIR = os.path.join(BASE_DIR, "Bots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(BOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ================= HELPERS =================
def bot_path(name):
    return os.path.join(BOTS_DIR, name)

def main_file(name):
    path = os.path.join(bot_path(name), "main.txt")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

# ================= ROUTES =================
@app.route("/")
def index():
    bots = []
    for b in os.listdir(BOTS_DIR):
        if os.path.isdir(bot_path(b)):
            bots.append({"name": b, "status": status(b)})
    return render_template("index.html", bots=bots)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        zip_file = request.files.get("zip")
        main = request.form.get("main")

        if not zip_file or not main:
            flash("ZIP file and main file name are required")
            return redirect(url_for("upload"))

        if not zip_file.filename.endswith(".zip"):
            flash("Only ZIP files are allowed")
            return redirect(url_for("upload"))

        name = os.path.splitext(zip_file.filename)[0]
        path = bot_path(name)
        os.makedirs(path, exist_ok=True)

        zip_path = os.path.join(path, zip_file.filename)
        zip_file.save(zip_path)

        try:
            safe_extract_zip(zip_path, path)
        except Exception:
            flash("Failed to extract ZIP file")
            return redirect(url_for("upload"))
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

        with open(os.path.join(path, "main.txt"), "w", encoding="utf-8") as f:
            f.write(main.strip())

        log_file = os.path.join(LOGS_DIR, f"{name}.log")
        install_requirements_async(path, log_file)

        flash("Bot uploaded. Dependencies installing in background.")
        return redirect(url_for("index"))

    return render_template("upload.html")


@app.route("/bot/<name>")
def bot_page(name):
    if not os.path.isdir(bot_path(name)):
        abort(404)
    return render_template("bot.html", name=name, status=status(name))


@app.route("/start/<name>")
def start(name):
    mf = main_file(name)
    if not mf:
        flash("Main file not set")
        return redirect(f"/bot/{name}")
    start_bot(name, mf)
    return redirect(f"/bot/{name}")


@app.route("/stop/<name>")
def stop(name):
    stop_bot(name)
    return redirect(f"/bot/{name}")


@app.route("/logs/<name>")
def logs(name):
    if not os.path.isdir(bot_path(name)):
        abort(404)
    return render_template("logs.html", name=name, logs=get_logs(name))


@app.route("/logs_raw/<name>")
def logs_raw(name):
    if not os.path.isdir(bot_path(name)):
        abort(404)
    return get_logs(name)


# ================= MANUAL DEPENDENCY INSTALL =================
@app.route("/install_dep/<name>", methods=["POST"])
def install_dep(name):
    bot_dir = bot_path(name)
    if not os.path.isdir(bot_dir):
        abort(404)

    pkg = request.form.get("package")
    if not pkg:
        return jsonify({"status": "error", "msg": "No package provided"}), 400

    log_file = os.path.join(LOGS_DIR, f"{name}.log")

    def run_install():
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n📦 Installing dependency: {pkg}...\n")
            subprocess.call(
                ["pip", "install", pkg],
                cwd=bot_dir,
                stdout=f,
                stderr=f
            )
            f.write(f"✅ Installed: {pkg}\n")

    threading.Thread(target=run_install, daemon=True).start()
    return jsonify({"status": "ok", "msg": f"Installing {pkg} in background"})


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
