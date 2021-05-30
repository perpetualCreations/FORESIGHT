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
from time import time, sleep


test_signal = False


def handle(instance, connection_socket, client_id: int):
    """Handle FORESIGHT interface clients."""
    global test_signal
    is_event_updater = False
    swbs.Instance.send(instance, "REQUEST TYPE", connection_socket)
    type_declaration = swbs.Instance.receive(instance,
                                             socket_instance=connection_socket)
    if type_declaration != "FORESIGHT":
        swbs.Instance.send(instance, "ABORT", connection_socket)
        swbs.Instance.close(instance)
        print(type_declaration)
        raise Exception("Client isn't a FORESIGHT instance!")
    else:
        swbs.Instance.send(instance, "OK", connection_socket)
    while True:
        if is_event_updater is True:
            swbs.Instance.send(instance, "exampleTextDisplayBox TEXT",
                               connection_socket)
            swbs.Instance.receive(instance, socket_instance=connection_socket)
            swbs.Instance.send(instance,
                               "Hello world! UNIX TIME: " + str(time()),
                               connection_socket)
            if test_signal is True:
                test_signal = False
                swbs.Instance.send(instance,
                                   "exampleTextDisplayLabel TEXT",
                                   connection_socket)
                swbs.Instance.receive(instance,
                                      socket_instance=connection_socket)
                swbs.Instance.send(instance,
                                   "Press it again to update. UNIX TIME: " +
                                   str(time()), connection_socket)
        else:
            command = swbs.Instance.receive(instance,
                                            socket_instance=connection_socket)
            if command == "UPDATE":
                is_event_updater = True
                swbs.Instance.send(instance, "OK", connection_socket)
                continue
            if command in ["BACKEND_COMMAND_SENDING_TEXT",
                           "BACKEND_COMMAND_SENDING_TEXT_BOX"]:
                swbs.Instance.send(instance, "OK", connection_socket)
                print(swbs.Instance.receive(instance,
                                            socket_instance=connection_socket))
            else:
                test_signal = True
            print(command)


server = swbs.Server(42069, None, connection_handler=handle)

while True:
    pass
