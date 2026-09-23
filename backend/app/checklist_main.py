from flask import Flask, redirect
from flask_cors import CORS

from .routes.api import api_bp
from .routes.configuracoes import checklist_bp


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    CORS(app)
    app.register_blueprint(api_bp)
    app.register_blueprint(checklist_bp)

    @app.route("/")
    def index():
        return redirect("/checklist")

    return app


app = create_app()