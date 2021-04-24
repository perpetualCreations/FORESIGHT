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

config = configparser.ConfigParser()
config.read("main.cfg")
application = flask.Flask(__name__)
application.secret_key = urandom(4096)
login_manager = flask_login.LoginManager()
login_manager.init_app(application)
login_manager.login_view = "/"


class User(flask_login.UserMixin):
    """
    Abstraction of administrator user.
    """


@login_manager.user_loader
def load_user(user_id):
    """
    Login user loader.

    :param user_id: str
    """
    return User.get_id(user_id)


@application.route("/", methods=["GET", "POST"])
def index():
    """
    Forward to index.html, for login page.
    Accepts

    :return: flask.render_template
    """
    return flask.render_template("index.html", serverid=config["CORE"]["ID"])


@application.route("/auth", methods=["POST"])
def auth():
    """
    POST endpoint for login authentication.

    :return: None
    """
    form = json.loads(flask.request.data)


if __name__ == "__main__":
    application.run(debug=False, port=80)
