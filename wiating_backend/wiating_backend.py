# -*- coding: utf-8 -*-

"""Python Flask Wiating API backend
"""
from werkzeug.exceptions import HTTPException

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_gzip import Gzip

from .image import images
from .logs import logs
from .points import points
from .user_management import user_mgmt


def configure_blueprints(app):
    """Configure blueprints in views."""

    with app.app_context():
        for bp in [images, logs, points, user_mgmt]:
            app.register_blueprint(bp)


def configure_app(app, config):
    app.config.from_object(config)


def configure_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_auth_error(ex):
        response = jsonify(message=str(ex))
        response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
        return response


def configure_home(app):
    @app.route('/')
    def home():
        return render_template('home.html')


def health_check(app):
    @app.route('/healthz')
    def healthz():
        return {}, 200


def configure_compression(app):
    app = Gzip(app)


def create_app(config):
    app = Flask(__name__, static_url_path=config.FLASK_STATIC_PATH, static_folder=config.FLASK_STATIC_FOLDER)
    configure_app(app, config)
    configure_blueprints(app)
    configure_home(app)
    configure_compression(app)
    health_check(app)

    CORS(app)
    return app
