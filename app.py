import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash
from bot_manager import start_bot, stop_bot, status, get_logs
from utils import safe_extract_zip

app = Flask(__name__)
app.secret_key = "secure-panel-key"

BOTS_DIR = "Bots"
os.makedirs(BOTS_DIR, exist_ok=True)

@app.route("/")
def index():
    bots = []
    for b in os.listdir(BOTS_DIR):
        bots.append({"name": b, "status": status(b)})
    return render_template("index.html", bots=bots)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        zipf = request.files.get("zip")
        main_file = request.form.get("main")

        if not zipf or not main_file:
            flash("Missing fields")
            return redirect("/upload")

        bot_name = zipf.filename.replace(".zip", "")
        bot_path = os.path.join(BOTS_DIR, bot_name)
        os.makedirs(bot_path, exist_ok=True)

        zip_path = os.path.join(bot_path, zipf.filename)
        zipf.save(zip_path)

        safe_extract_zip(zip_path, bot_path)
        os.remove(zip_path)

        if os.path.exists(os.path.join(bot_path, "requirements.txt")):
            subprocess.call(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=bot_path
            )

        with open(os.path.join(bot_path, "main.txt"), "w") as f:
            f.write(main_file.strip())

        return redirect("/")

    return render_template("upload.html")

@app.route("/bot/<name>")
def bot(name):
    return render_template("bot.html", name=name, status=status(name))

@app.route("/start/<name>")
def start(name):
    main = open(f"{BOTS_DIR}/{name}/main.txt").read().strip()
    start_bot(name, main)
    return redirect(f"/bot/{name}")

@app.route("/stop/<name>")
def stop(name):
    stop_bot(name)
    return redirect(f"/bot/{name}")

@app.route("/logs/<name>")
def logs(name):
    return render_template("logs.html", name=name, logs=get_logs(name))

if __name__ == "__main__":
    app.run()
