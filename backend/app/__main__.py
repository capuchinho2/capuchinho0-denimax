import os
from flask import Flask
from flask_cors import CORS
from .routes.conferencia import conferencia_bp
from .routes.dashboard import dashboard_bp
from .routes.status_prep import status_prep_bp
from .routes.api import api_bp
from .routes.rastreabilidade import rastreabilidade_bp
from .routes.preparacao import bp_preparacao
from .routes.configuracoes import configuracoes_bp
from .routes.produtividade_operador import produtividade_operador_bp
from .routes.produtividade_carregador import produtividade_carregador_bp
from .routes.produtividade_preparador import produtividade_preparador_bp

def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "static")
    templates_dir = os.path.join(base_dir, "templates")
    
    app = Flask(__name__, static_folder=static_dir, template_folder=templates_dir)
    CORS(app)

    # Registrar blueprints
    app.register_blueprint(conferencia_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(status_prep_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(rastreabilidade_bp)
    app.register_blueprint(bp_preparacao)
    app.register_blueprint(configuracoes_bp)
    app.register_blueprint(produtividade_operador_bp)
    app.register_blueprint(produtividade_carregador_bp)
    app.register_blueprint(produtividade_preparador_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
