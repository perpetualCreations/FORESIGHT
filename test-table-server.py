"""
Test-Table-Server.

Test back-end server for validating FORESIGHT table interface.
"""

import swbs

server = swbs.Host(42068, None)
server.listen()
server.send("REQUEST TYPE")
if server.receive() != "FORESIGHT":
    raise Exception("Client isn't a FORESIGHT instance!")
while True:
    server.receive()
    if server.receive() == "GET_TABLE":
        server.send("[]")
