var socket = io();

socket.on("eventUpdate", data => {
    if (data["type"] == "TEXT") {
        /* set value for textarea and textContent for paragraphs */
        document.getElementById(data["id"]).value = data["data"];
        document.getElementById(data["id"]).textContent = data["data"];
    }
    else if (data["type"] == "TABLE") {
        /* scripting for populating target table */
        document.getElementById(data["id"] + "TableContent").innerHTML = "";
        for (row in data["data"]) {
            document.getElementById(data["id"] + "TableContent").innerHTML += "<tr>";
            for (column in row) {
                document.getElementById(data["id"] + "TableContent").innerHTML += ("<td>" + column + "</td>"); 
            }
            document.getElementById(data["id"] + "TableContent").innerHTML += "</tr>"
        }
    }
});

socket.on("logError", data => {
    document.getElementById("errors").style.display = "initial";
    document.getElementById("error-log").innerHTML += "<p>[" + data["timestamp"] + "]: " + data["message"] + "</p>"
});

function dispatchCommand(command, interface, type, payload) {
    /* dispatch commands for button, textEntry, textEntryBox */
    socket.emit("command", {"command": command, "interface": interface, "requestType": type, "payload": payload});
}
