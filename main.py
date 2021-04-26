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
import configparser
import json
import swbs
import threading
from os import urandom
from ast import literal_eval
from hashlib import sha3_512

config = configparser.ConfigParser()
config.read("main.cfg")
application = flask.Flask(__name__)
application.secret_key = urandom(4096)
login_manager = flask_login.LoginManager()
login_manager.init_app(application)
login_manager.login_view = "login"
users = {"username": "admin"}

with open("interfaces.json") as interface_config_handler:
    interfaces = json.load(interface_config_handler)

try:
    del interfaces["__docs"]
except KeyError:
    pass

for interface in list(interfaces.keys()):
    if interfaces[interface]["isExample"] is True:
        del interfaces[interface]


class User(flask_login.UserMixin):
    """
    Flask user model. Refer to documentation of Flask-Login for more information.
    """
    pass


class InterfaceClient(swbs.Client):
    def __init__(self, host, port, key, key_is_path):
        super().__init__(host, port, key, key_is_path)


@login_manager.user_loader
def user_loader(user_id) -> User:
    user = User()
    user.id = user_id
    return user


@application.route("/")
@flask_login.login_required
def index() -> any:
    """
    Renders index.html when root is requested.
    Serves as homepage with control panels.

    Requires login.

    :return: any
    """
    return flask.render_template("index.html", serverid=config["CORE"]["ID"], interfaces=interfaces)


@application.route("/password/", methods=["GET", "POST"])
@flask_login.login_required
def change_password() -> any:
    """
    Renders change_password.html when requested with GET.
    Serves as utility page for changing the admin password.
    Validates and commits password change when requested with POST.
    Re-renders page with an error message if re-typed password is different.

    Requires login.

    :return: any
    """
    if flask.request.method == "GET":
        return flask.render_template("change_password.html", serverid=config["CORE"]["ID"], error="")
    elif flask.request.method == "POST":
        if flask.request.form["password"] == flask.request.form["password_affirm"]:
            config["CORE"]["PASSWORD"] = sha3_512(flask.request.form["password"].encode("ascii")).hexdigest()
            with open("main.cfg", "wb") as config_overwrite:
                config.write(config_overwrite)
            return flask.redirect(flask.url_for("index"))
        else:
            return flask.render_template("change_password.html", serverid=config["CORE"]["ID"],
                                         error="Passwords don't match.", form=flask.request.form)
    else:
        flask.abort(405)


@application.route("/login/", methods=["GET", "POST"])
def login() -> any:
    """
    Renders login.html when requested with GET.
    Serves as login page for users to authenticate themselves.
    Validates password submissions when requested with POST, and redirects to root.
    Re-renders page with an error message if password is invalid when compared to hash.

    :return: any
    """
    if flask.request.method == "GET":
        return flask.render_template("login.html", serverid=config["CORE"]["ID"], error="")
    elif flask.request.method == "POST":
        if sha3_512(flask.request.form["password"].encode("ascii", "replace")).hexdigest() == \
                config["CORE"]["PASSWORD"]:
            user = User()
            user.id = users["username"]
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("index"))
        else:
            return flask.render_template("login.html", serverid=config["CORE"]["ID"], error="Invalid password.")
    else:
        flask.abort(405)


@application.route("/logout/")
@flask_login.login_required
def logout() -> any:
    """
    Logs out user session, and redirects to login page.

    Requires login.

    :return: any
    """
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login"))


if __name__ == "__main__":
    application.run(debug=literal_eval(config["CORE"]["DEBUG"]), port=int(config["NET"]["PORT"]))
