import subprocess
import os
import threading

BOTS_DIR = "Bots"
LOGS_DIR = "logs"

os.makedirs(LOGS_DIR, exist_ok=True)

running_bots = {}

def stream_logs(process, log_file):
    with open(log_file, "a", encoding="utf-8") as f:
        for line in iter(process.stdout.readline, b""):
            f.write(line.decode(errors="ignore"))
            f.flush()

def start_bot(bot_name, main_file):
    bot_path = os.path.join(BOTS_DIR, bot_name)
    file_path = os.path.join(bot_path, main_file)

    if not os.path.exists(file_path):
        return False, "Main file not found"

    log_file = os.path.join(LOGS_DIR, f"{bot_name}.log")

    process = subprocess.Popen(
        ["python", main_file],
        cwd=bot_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1
    )

    thread = threading.Thread(
        target=stream_logs,
        args=(process, log_file),
        daemon=True
    )
    thread.start()

    running_bots[bot_name] = process
    return True, process.pid

def stop_bot(bot_name):
    process = running_bots.get(bot_name)
    if not process:
        return False

    process.terminate()
    process.wait()
    del running_bots[bot_name]
    return True

def bot_status(bot_name):
    process = running_bots.get(bot_name)
    if process and process.poll() is None:
        return "Running"
    return "Stopped"

def read_logs(bot_name):
    log_file = os.path.join(LOGS_DIR, f"{bot_name}.log")
    if not os.path.exists(log_file):
        return ""
    with open(log_file, "r", encoding="utf-8") as f:
        return f.read()[-5000:]