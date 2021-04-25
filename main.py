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


@application.route("/auth/", methods=["POST"])
def login_auth():
    if flask.request.method == "POST":
        if sha3_512(flask.request.form["password"].encode("ascii", "replace")).hexdigest() == \
                config["CORE"]["PASSWORD"]:
            user = User()
            user.id = users["username"]
            flask_login.login_user(user)
            flask.flash("Login successful.", "info")
            return flask.redirect(flask.url_for("index"))
        else:
            return flask.render_template("login.html")
    else:
        flask.abort(405)


@application.route("/login/")
def login():
    return flask.render_template("login.html", serverid=config["CORE"]["ID"])


@application.route("/logout/")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login"))


if __name__ == "__main__":
    application.run(debug=literal_eval(config["CORE"]["DEBUG"]), port=int(config["NET"]["PORT"]))
