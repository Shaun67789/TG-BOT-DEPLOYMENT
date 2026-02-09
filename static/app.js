// Manual dependency installer
function installDep(botName){
    const input = document.getElementById("dep-input-" + botName);
    if(!input.value) return alert("Enter package name");

    fetch("/install_dep/" + botName, {
        method:"POST",
        headers:{"Content-Type":"application/x-www-form-urlencoded"},
        body:"package=" + encodeURIComponent(input.value)
    })
    .then(r=>r.json())
    .then(data=>{
        alert(data.msg);
        input.value="";
    })
    .catch(e=>alert("Install failed"));
}
