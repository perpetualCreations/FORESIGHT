"""
Test-Table-Server.

Test back-end server for validating FORESIGHT table interface.
"""

import swbs
from time import time, sleep


def handle(instance, connection_socket, client_id: int):
    """Handle FORESIGHT interface clients."""
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
            swbs.Instance.send(instance, "testingTable TABLE",
                               connection_socket)
            swbs.Instance.receive(instance, socket_instance=connection_socket)
            swbs.Instance.send(instance,
                               "[['Test'], ['" + str(time()) + "']]",
                               connection_socket)
            sleep(5)
        else:
            command = swbs.Instance.receive(instance,
                                            socket_instance=connection_socket)
            if command == "UPDATE":
                is_event_updater = True
                swbs.Instance.send(instance, "OK", connection_socket)
                continue


server = swbs.Server(42068, None, connection_handler=handle)

while True:
    pass
