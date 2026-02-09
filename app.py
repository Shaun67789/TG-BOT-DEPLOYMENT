import os
import zipfile
import subprocess
from flask import Flask, render_template, request, redirect, url_for
from bot_manager import start_bot, stop_bot, bot_status, read_logs

app = Flask(__name__)

BOTS_DIR = "Bots"
os.makedirs(BOTS_DIR, exist_ok=True)

@app.route("/")
def index():
    bots = []
    for bot in os.listdir(BOTS_DIR):
        bots.append({
            "name": bot,
            "status": bot_status(bot)
        })
    return render_template("index.html", bots=bots)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        zip_file = request.files["zip"]
        main_file = request.form["main_file"]

        bot_name = zip_file.filename.replace(".zip", "")
        bot_path = os.path.join(BOTS_DIR, bot_name)
        os.makedirs(bot_path, exist_ok=True)

        zip_path = os.path.join(bot_path, zip_file.filename)
        zip_file.save(zip_path)

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(bot_path)

        os.remove(zip_path)

        if os.path.exists(os.path.join(bot_path, "requirements.txt")):
            subprocess.call(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=bot_path
            )

        with open(os.path.join(bot_path, "main.txt"), "w") as f:
            f.write(main_file)

        return redirect(url_for("index"))

    return render_template("upload.html")

@app.route("/bot/<name>")
def bot_page(name):
    return render_template(
        "bot.html",
        name=name,
        status=bot_status(name)
    )

@app.route("/start/<name>")
def start(name):
    bot_path = os.path.join(BOTS_DIR, name)
    main_file = open(os.path.join(bot_path, "main.txt")).read()
    start_bot(name, main_file)
    return redirect(url_for("bot_page", name=name))

@app.route("/stop/<name>")
def stop(name):
    stop_bot(name)
    return redirect(url_for("bot_page", name=name))

@app.route("/logs/<name>")
def logs(name):
    content = read_logs(name)
    return render_template("logs.html", name=name, logs=content)

if __name__ == "__main__":
    app.run(debug=True)