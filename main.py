"""
███████╗ ██████╗ ██████╗ ███████╗███████╗██╗ ██████╗ ██╗  ██╗████████╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝
█████╗  ██║   ██║██████╔╝█████╗  ███████╗██║██║  ███╗███████║   ██║
██╔══╝  ██║   ██║██╔══██╗██╔══╝  ╚════██║██║██║   ██║██╔══██║   ██║
██║     ╚██████╔╝██║  ██║███████╗███████║██║╚██████╔╝██║  ██║   ██║
╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝

Project FORESIGHT
"""

import flask
import flask_login
import flask_socketio
import configparser
import json
import swbs
import jinja2
import threading
from os import urandom
from ast import literal_eval
from hashlib import sha3_512
from functools import wraps
from time import sleep
from random import choices
from string import ascii_lowercase


config = configparser.ConfigParser()
config.read("main.cfg")
application = flask.Flask(__name__)
application.secret_key = urandom(4096)
login_manager = flask_login.LoginManager()
login_manager.init_app(application)
login_manager.login_view = "login"
users = {"username": "admin"}
socket_io = flask_socketio.SocketIO(application)

interface_template_loader = jinja2.FileSystemLoader(searchpath="interfaces/")
interface_template_environment = jinja2.Environment(
    loader=interface_template_loader)

pollers = []

with open("interfaces.json") as interface_config_handler:
    interfaces = json.load(interface_config_handler)

try:
    del interfaces["__docs"]
except KeyError:
    pass


class User(flask_login.UserMixin):
    """Flask user model."""


@login_manager.user_loader
def user_loader(user_id) -> User:
    """Flask Login function required for loading the admin user."""
    user = User()
    user.id = user_id
    return user


@socket_io.on("connect")
def connect_handler() -> any:
    """Handle websocket connections, checking for login auth."""
    if flask_login.current_user.is_authenticated is not True:
        return False


class InterfaceClient(swbs.Client):
    """Socket interface instance class."""

    def __init__(self, host, port, key, key_is_path):
        """Class initialization."""
        super().__init__(host, port, key, key_is_path)

    def connect_wrapper(self) -> None:
        """
        Serve as a wrapper for swbs.Client.connect.

        Has additional calls to specify ARIA protocol.

        :return: None
        """
        InterfaceClient.connect(self)
        if InterfaceClient.receive(self) == "REQUEST TYPE":
            InterfaceClient.send(self, "FORESIGHT")
        else:
            InterfaceClient.send(self, "KEYERROR")
            raise Exception("Failed to initialize interface host!")


@socket_io.on("pollUpdate")
def poll_data_broadcaster(data: dict):
    """Emit event pollUpdate to all clients as a broadcast."""
    with application.app_context():
        flask_socketio.emit("pollUpdate", data, json=True, broadcast=True,
                            namespace="/")


def interface_client_poller(target_interface: str, target_section: str,
                            target_element: str) -> None:
    """
    Thread for textDisplayLabel and textDisplayBox element polling.

    :param target_interface: str, key for target interface
    :param target_section: str, key for target interface section
    :param target_element: str, key for target interface element
    :return: None
    """
    while True:
        while flask_login.current_user is None:
            pass
        interfaces[target_interface]["interface_client_lock"].acquire(
            blocking=True)
        interfaces[target_interface]["interface_client"].send(
            interfaces[target_interface]["sections"][target_section]
            [target_element]["command"])
        poll_data_broadcaster(
            {"data": interfaces[target_interface]
             ["interface_client"].receive(), "id": interfaces[target_interface]
             ["sections"][target_section][target_element]["id"]})
        interfaces[target_interface]["interface_client_lock"].release()
        sleep(float(interfaces[target_interface
                               ]["sections"][target_section
                                             ][target_element][
                                                 "pollRateInSeconds"]))


for interface in list(interfaces.keys()):
    content = []
    if interfaces[interface]["isExample"] is True:
        del interfaces[interface]
        continue
    else:
        interfaces[interface].update({"interface_client": InterfaceClient(
            interfaces[interface]["host"], int(interfaces[interface]["port"]),
            interfaces[interface]["auth"], interfaces[interface]["authIsPath"]
            )})
        interfaces[interface]["interface_client"].connect_wrapper()
        interfaces[interface].update({"interface_client_lock":
                                      threading.Lock()})
        for section in interfaces[interface]["sections"]:
            interface_elements = ""
            for element in interfaces[interface]["sections"][section]:
                if isinstance(interfaces[interface]["sections"][section]
                              [element], dict) is True:
                    interfaces[interface]["sections"][section][element].update(
                        {"id": ''.join(choices(ascii_lowercase, k=128))})
                    interfaces[interface]["sections"][section][element].update(
                        {"parent_interface": interface})
                    interface_elements += \
                        interface_template_environment.get_template(
                            interfaces[interface]["sections"][section][element]
                            ["type"] + ".html").render(
                                **interfaces[interface]["sections"][section]
                                [element])
                    if interfaces[interface]["sections"][section][element][
                            "type"] in ["textDisplayBox", "textDisplayLabel"]:
                        pollers.append(threading.Thread(
                            target=interface_client_poller,
                            args=(interface, section, element), daemon=True
                            ).start())
                else:
                    continue
            content.append(interface_template_environment.get_template(
                interfaces[interface]["sections"][section]["type"] + ".html"
                ).render(label=interfaces[interface]["sections"][section]
                         ["label"], interfaces=interface_elements))

        interfaces[interface].update({"sections_render": content})


@socket_io.on("command")
def command_handler(json_payload) -> None:
    """Handle websocket command request events from clients."""
    json_payload = str(json_payload).replace("'", '"')
    command_payload = json.loads(json_payload)
    interfaces[command_payload["interface"]
               ]["interface_client_lock"].acquire(blocking=True)
    if command_payload["requestType"] == "SIGNAL":
        interfaces[command_payload["interface"]
                   ]["interface_client"].send(command_payload["command"])
    elif command_payload["requestType"] == "PAYLOAD":
        interfaces[command_payload["interface"]
                   ]["interface_client"].send(command_payload["command"])
        interfaces[command_payload["interface"]
                   ]["interface_client"].receive()
        interfaces[command_payload["interface"]
                   ]["interface_client"].send(command_payload["payload"])
    interfaces[command_payload["interface"]
               ]["interface_client_lock"].release()


@application.route("/")
@flask_login.login_required
def index() -> any:
    """
    Render index.html when root is requested.

    Serves as homepage with control panels.

    Requires login.

    :return: any
    """
    return flask.render_template("index.html", serverid=config["CORE"]["ID"],
                                 interfaces=interfaces)


@application.route("/password/", methods=["GET", "POST"])
@flask_login.login_required
def change_password() -> any:
    """
    Render change_password.html when requested with GET.

    Serves as utility page for changing the admin password.
    Validates and commits password change when requested with POST.
    Re-renders page with an error message if re-typed password is different.
    Requires login.

    :return: any
    """
    if flask.request.method == "GET":
        return flask.render_template("change_password.html",
                                     serverid=config["CORE"]["ID"], error="")
    elif flask.request.method == "POST":
        if flask.request.form["password"] == \
                flask.request.form["password_affirm"]:
            config["CORE"]["PASSWORD"
                           ] = sha3_512(
                               flask.request.form["password"
                                                  ].encode("ascii")
                                                  ).hexdigest()
            with open("main.cfg", "wb") as config_overwrite:
                config.write(config_overwrite)
            return flask.redirect(flask.url_for("index"))
        else:
            return flask.render_template("change_password.html",
                                         serverid=config["CORE"]["ID"],
                                         error="Passwords don't match.",
                                         form=flask.request.form)
    else:
        flask.abort(405)


@application.route("/login/", methods=["GET", "POST"])
def login() -> any:
    """
    Render login.html when requested with GET.

    Serves as login page for users to authenticate themselves.
    Validates password submissions when requested with POST,
    and redirects to root.
    Re-renders page with an error message if password is invalid
    when compared to hash.

    :return: any
    """
    if flask.request.method == "GET":
        if flask_login.current_user.is_authenticated is True:
            return flask.redirect(flask.url_for("index"))
        else:
            return flask.render_template("login.html",
                                         serverid=config["CORE"]["ID"],
                                         error="")
    elif flask.request.method == "POST":
        if sha3_512(flask.request.form["password"].encode("ascii", "replace")
                    ).hexdigest() == config["CORE"]["PASSWORD"]:
            user = User()
            user.id = users["username"]
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("index"))
        else:
            return flask.render_template("login.html",
                                         serverid=config["CORE"]["ID"],
                                         error="Invalid password.")
    else:
        flask.abort(405)


@application.route("/logout/")
@flask_login.login_required
def logout() -> any:
    """
    Log out user session, and redirect to login page.

    Requires login.

    :return: any
    """
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login"))


if __name__ == "__main__":
    socket_io.run(application, debug=literal_eval(config["CORE"]["DEBUG"]),
                  port=int(config["NET"]["PORT"]), use_reloader=False)
