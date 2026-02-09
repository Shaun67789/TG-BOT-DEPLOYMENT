// app.js — UI helpers (safe for Render)

function disableButton(btn, text) {
    btn.innerText = text;
    btn.style.opacity = "0.6";
    btn.style.pointerEvents = "none";
}

function startBot(botName, btn) {
    disableButton(btn, "Starting...");
    window.location.href = `/start/${botName}`;
}

function stopBot(botName, btn) {
    disableButton(btn, "Stopping...");
    window.location.href = `/stop/${botName}`;
}

// Live logs (AJAX, no page refresh)
function startLogStream(botName) {
    const box = document.getElementById("log-box");
    if (!box) return;

    setInterval(() => {
        fetch(`/logs_raw/${botName}`)
            .then(r => r.text())
            .then(t => {
                box.textContent = t;
                box.scrollTop = box.scrollHeight;
            })
            .catch(() => {});
    }, 2000);
}
