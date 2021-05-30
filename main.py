"""
Project FORESIGHT.

███████╗ ██████╗ ██████╗ ███████╗███████╗██╗ ██████╗ ██╗  ██╗████████╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝
█████╗  ██║   ██║██████╔╝█████╗  ███████╗██║██║  ███╗███████║   ██║
██╔══╝  ██║   ██║██╔══██╗██╔══╝  ╚════██║██║██║   ██║██╔══██║   ██║
██║     ╚██████╔╝██║  ██║███████╗███████║██║╚██████╔╝██║  ██║   ██║
╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝

Made by perpetualCreations
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
from datetime import datetime, timezone


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

errors = []


@socket_io.on("logError")
def log_error_broadcaster(message: str):
    """Emit event logError to all clients as a broadcast."""
    error = {"timestamp":
             datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
             "message": message}
    errors.append(error)
    with application.app_context():
        flask_socketio.emit("logError", error, json=True, broadcast=True,
                            namespace="/")


try:
    with open("interfaces.json") as interface_config_handler:
        interfaces = json.load(interface_config_handler)
    with open("extended.json") as extended_interface_config_location_handler:
        extended_interface_configs = \
            json.load(extended_interface_config_location_handler)
    for extended_interface_for_loading in extended_interface_configs:
        with open(extended_interface_for_loading
                  ) as extended_interface_config_handler:
            interfaces.update(json.load(extended_interface_config_handler))
except Exception as ParentException:
    error_string = str(ParentException) + " -> " + \
        "Failed to load interface configurations."
    print(error_string)
    log_error_broadcaster(error_string)


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
    else:
        with application.app_context():
            for error in errors:
                flask_socketio.emit("logError", error, json=True)


class InterfaceClient(swbs.Client):
    """Socket interface instance class."""

    def __init__(self, host, port, key, key_is_path):
        """Class initialization."""
        super().__init__(host, port, key, key_is_path)
        self.dead = False

    def connect_wrapper(self) -> None:
        """
        Serve as a wrapper for swbs.Client.connect.

        Has additional calls to specify ARIA protocol.

        :param is_update: if True, inform server to operate in event-update
        :type is_update: bool
        :return: None
        """
        try:
            InterfaceClient.connect(self)
            type_request = InterfaceClient.receive(self)
            if type_request == "REQUEST TYPE":
                InterfaceClient.send(self, "FORESIGHT")
                if InterfaceClient.receive(self) == "ABORT":
                    InterfaceClient.disconnect()
                    error_string = "Host " + self.host + " raised ABORT. " + \
                        "Interface client will shutdown."
                    self.dead = True
            else:
                InterfaceClient.send(self, "KEYERROR")
                InterfaceClient.disconnect()
                error_string = "Host " + self.host + \
                    " failed to send host request type, expected " + \
                    '"REQUEST TYPE"' + ", got " + type_request + "." + \
                    " Interface client will shutdown."
                print(error_string)
                log_error_broadcaster(error_string)
                self.dead = True
        except Exception as ParentException:
            error_string = "Failed to initialize interface host " + \
                "connecting to " + self.host + " on port " + str(self.port) + \
                ". Interface client will shutdown."
            print(str(ParentException) + " -> " + error_string)
            log_error_broadcaster(error_string)
            self.dead = True


@socket_io.on("eventUpdate")
def event_data_broadcaster(data: dict):
    """Emit event eventUpdate to all clients as a broadcast."""
    with application.app_context():
        flask_socketio.emit("eventUpdate", data, json=True, broadcast=True,
                            namespace="/")


@socket_io.on("command")
def command_handler(json_payload) -> None:
    """Handle websocket command request events from clients."""
    json_payload = str(json_payload).replace("'", '"')
    command_payload = json.loads(json_payload)
    if interfaces[command_payload["interface"]]["interface_client"].dead is \
            True:
        return None
    if command_payload["requestType"] == "SIGNAL":
        interfaces[command_payload["interface"]
                   ]["interface_client"].send(command_payload["command"])
    elif command_payload["requestType"] == "PAYLOAD":
        interfaces[command_payload["interface"]
                   ]["interface_client"].send(command_payload["command"])
        if interfaces[
            command_payload["interface"]]["interface_client"].receive() \
                == "KEYERROR":
            error_string = "Payload command " + \
                command_payload["command"] + " is invalid."
            print(error_string)
            log_error_broadcaster(error_string)
            return None
        interfaces[command_payload["interface"]
                   ]["interface_client"].send(command_payload["payload"])
    else:
        error_string = "Received invalid requestType, expected " + \
            '"SIGNAL" or "PAYLOAD", got ' + \
            command_payload["requestType"] + ". Request ignored."
        print(error_string)
        log_error_broadcaster(error_string)


def interface_client_event_listener(target_interface: str) -> None:
    """
    Thread for updating textDisplayLabel, textDisplayBox, and table elements.

    :param interface: name of interface
    :type target_interface: str
    :return: None
    """
    set_update = False
    while interfaces[target_interface]["interface_client_update"].dead is \
            False:
        while flask_login.current_user is None:
            pass
        if set_update is False:
            interfaces[target_interface]["interface_client_update"
                                         ].send("UPDATE")
            if interfaces[target_interface]["interface_client_update"
                                            ].receive() == "OK":
                set_update = True
                continue
            else:
                error_string = "Host for interface " + target_interface + \
                    " does not support event updating, any display " + \
                    "elements in the interfacce will not update. " + \
                    "Exiting listener."
                print(error_string)
                log_error_broadcaster(error_string)
                return None
        update_header_data = \
            interfaces[target_interface]["interface_client_update"
                                         ].receive().split(" ")
        if len(update_header_data) == 2 and \
                update_header_data[1] in ["TEXT", "TABLE"]:
            interfaces[target_interface]["interface_client_update"].send("OK")
            update_content_data = \
                interfaces[target_interface][
                    "interface_client_update"].receive()
            if update_header_data[1] == "TABLE":
                update_content_data = literal_eval(update_content_data)
            event_data_broadcaster(
                {"data": update_content_data,
                 "id": update_header_data[0],
                 "type": update_header_data[1]})
        else:
            interfaces[target_interface][
                "interface_client_update"].send("KEYERROR")
            error_string = "Received update with invalid header, " + \
                "for interface " + target_interface + ", content: " + \
                str(update_header_data)
            print(error_string)
            log_error_broadcaster(error_string)


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
        interfaces[interface].update(
            {"interface_client_update":
             InterfaceClient(interfaces[interface]["host"],
                             int(interfaces[interface]["port"]),
                             interfaces[interface]["auth"],
                             interfaces[interface]["authIsPath"])})
        interfaces[interface]["interface_client"].connect_wrapper()
        interfaces[interface].update({"interface_client_lock":
                                      threading.Lock()})
        interfaces[interface]["interface_client_update"].connect_wrapper()
        threading.Thread(target=interface_client_event_listener,
                         args=(interface,)).start()
        for section in interfaces[interface]["sections"]:
            interface_elements = ""
            for element in interfaces[interface]["sections"][section]:
                if isinstance(interfaces[interface]["sections"][section]
                              [element], dict) is True:
                    interfaces[interface]["sections"][section][element].update(
                        {"id": element})
                    interfaces[interface]["sections"][section][element].update(
                        {"parent_interface": interface})
                    interface_elements += \
                        interface_template_environment.get_template(
                            interfaces[interface]["sections"][section][element]
                            ["type"] + ".html").render(
                                **interfaces[interface]["sections"][section]
                                [element])
                else:
                    continue
            content.append(interface_template_environment.get_template(
                interfaces[interface]["sections"][section]["type"] + ".html"
                ).render(label=interfaces[interface]["sections"][section]
                         ["label"], interfaces=interface_elements))
        interfaces[interface].update({"sections_render": content})


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
