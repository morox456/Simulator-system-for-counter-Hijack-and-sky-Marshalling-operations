function startTraining() {

    let username = document.getElementById("username").value;

    if (username.trim() === "") {
        alert("Please enter your name.");
        return;
    }

    localStorage.setItem("username", username);

    window.location.href = "simulator.html";
}
