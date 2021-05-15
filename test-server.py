"""
Test-Server.

Test back-end server for validating FORESIGHT interfaces.
To use, point the hostname field of the to-be-tested interface under
interfaces.json to 127.0.0.1, port 42069, with no encryption.

Launch test-server.py and actual Flask application, get to clicking those
buttons.

Designed for the original example interface.
"""

import swbs
import json
from time import time


with open("interfaces.json") as interface_load_handle:
    interfaces = json.load(interface_load_handle)

commands = {}
test_interface = interfaces["NameOfBackendApplicationHere"]["sections"]

for section in test_interface:
    for element in test_interface[section]:
        current_element = test_interface[section][element]
        if isinstance(current_element, dict) is not True:
            continue
        if current_element["type"] in ["textEntry", "textEntryBox"]:
            commands.update({current_element["command"]: "PAYLOAD"})
        elif current_element["type"] == "button":
            commands.update({current_element["command"]: "SIGNAL"})
        elif current_element["type"] in ["textDisplayBox", "textDisplayLabel"]:
            commands.update({current_element["command"]: "POLL"})

server = swbs.Host(42069, None)
server.listen()
server.send("REQUEST TYPE")

if server.receive() != "FORESIGHT":
    server.send("ABORT")
    server.close()
    raise Exception("Client isn't a FORESIGHT instance!")

while True:
    request = server.receive()
    try:
        print("Accepted Request: ", request)
        if commands[request] == "PAYLOAD":
            server.send("OK!")
            print("Received (PAYLOAD): ", server.receive())
        elif commands[request] == "SIGNAL":
            print("Received (SIGNAL): ", request)
        elif commands[request] == "POLL":
            server.send("Hello World! UNIX: " + str(time()))
    except KeyError:
        print("Mangled Request: ", request)
