import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from bot_manager import start_bot, stop_bot, status, get_logs
from utils import safe_extract_zip, install_requirements_async

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BOTS_DIR = os.path.join(BASE_DIR, "Bots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(BOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def bot_path(name):
    return os.path.join(BOTS_DIR, name)

def main_file(name):
    p = os.path.join(bot_path(name), "main.txt")
    if not os.path.exists(p):
        return None
    return open(p).read().strip()

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
        zipf = request.files.get("zip")
        main = request.form.get("main")

        if not zipf or not main:
            flash("Missing fields")
            return redirect("/upload")

        if not zipf.filename.endswith(".zip"):
            flash("Only ZIP files allowed")
            return redirect("/upload")

        name = os.path.splitext(zipf.filename)[0]
        path = bot_path(name)
        os.makedirs(path, exist_ok=True)

        zip_path = os.path.join(path, zipf.filename)
        zipf.save(zip_path)

        safe_extract_zip(zip_path, path)
        os.remove(zip_path)

        with open(os.path.join(path, "main.txt"), "w") as f:
            f.write(main.strip())

        log_file = os.path.join(LOGS_DIR, f"{name}.log")
        install_requirements_async(path, log_file)

        flash("Bot uploaded. Dependencies installing in background.")
        return redirect("/")

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
    return render_template("logs.html", name=name, logs=get_logs(name))

@app.route("/logs_raw/<name>")
def logs_raw(name):
    return get_logs(name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
