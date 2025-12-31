from flask import Flask
from flask_cors import CORS
from app.routes.conferencia import conferencia_bp
from app.routes.dashboard import dashboard_bp
from app.routes.status_prep import status_prep_bp
from app.routes.api import api_bp
from app.routes.rastreabilidade import rastreabilidade_bp
from app.routes.preparacao import bp_preparacao
from app.routes.configuracoes import configuracoes_bp

def create_app():
    import os
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    app = Flask(__name__, static_folder=static_dir)
    CORS(app)

    # Registrar blueprints
    app.register_blueprint(conferencia_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(status_prep_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(rastreabilidade_bp)
    app.register_blueprint(bp_preparacao)
    app.register_blueprint(configuracoes_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
