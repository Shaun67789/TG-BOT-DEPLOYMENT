import subprocess
import os
import threading

BOTS_DIR = "Bots"
LOGS_DIR = "logs"

os.makedirs(LOGS_DIR, exist_ok=True)

running = {}

def _log_stream(proc, logfile):
    with open(logfile, "a", encoding="utf-8") as f:
        for line in iter(proc.stdout.readline, b""):
            if not line:
                break
            f.write(line.decode(errors="ignore"))
            f.flush()

def start_bot(bot_name, main_file):
    if bot_name in running:
        return False, "Already running"

    bot_path = os.path.join(BOTS_DIR, bot_name)
    main_path = os.path.join(bot_path, main_file)

    if not os.path.isfile(main_path):
        return False, "Main file not found"

    logfile = os.path.join(LOGS_DIR, f"{bot_name}.log")

    proc = subprocess.Popen(
        ["python", main_file],
        cwd=bot_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    t = threading.Thread(target=_log_stream, args=(proc, logfile), daemon=True)
    t.start()

    running[bot_name] = proc
    return True, proc.pid

def stop_bot(bot_name):
    proc = running.get(bot_name)
    if not proc:
        return False

    proc.terminate()
    proc.wait(timeout=5)
    del running[bot_name]
    return True

def status(bot_name):
    proc = running.get(bot_name)
    if proc and proc.poll() is None:
        return "Running"
    return "Stopped"

def get_logs(bot_name):
    path = os.path.join(LOGS_DIR, f"{bot_name}.log")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()[-8000:]
