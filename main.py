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


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(user_id):
    user = User()
    user.id = user_id
    return user


@application.route("/")
@flask_login.login_required
def index():
    return flask.render_template("index.html", serverid=config["CORE"]["ID"])


@application.route("/password/", methods=["GET", "POST"])
@flask_login.login_required
def change_password():
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
                                         error="Passwords don't match.")
    else:
        flask.abort(405)


@application.route("/login/", methods=["GET", "POST"])
def login():
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
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login"))


if __name__ == "__main__":
    application.run(debug=literal_eval(config["CORE"]["DEBUG"]), port=int(config["NET"]["PORT"]))
