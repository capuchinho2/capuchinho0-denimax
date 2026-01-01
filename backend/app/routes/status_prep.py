
from flask import Blueprint, render_template, request, jsonify
from ..utils.logic import obter_status_prep

status_prep_bp = Blueprint('status_prep', __name__)


@status_prep_bp.route('/status-prep')
def status_prep():
    return render_template('status_prep.html')

# Novo endpoint: Paletes Preparados (seguindo padrão de viagens pendentes)
@status_prep_bp.route('/status-prep/preparados', methods=['GET'])
def paletes_preparados():
    data_inicial = request.args.get('dataInicial')
    data_final = request.args.get('dataFinal')
    nome_preparador = request.args.get('preparador', '').strip()
    if not data_inicial or not data_final:
        return jsonify({"success": False, "error": "Parâmetros dataInicial e dataFinal são obrigatórios"}), 400
    try:
        resultado = obter_status_prep(data_inicial, data_final, nome_preparador)
        if not resultado.get('success'):
            return jsonify({"success": False, "error": "Erro ao obter dados"}), 500
        print("[DEBUG] Paletes preparados retornados:", resultado.get('viagens_preparadas', []))
        return jsonify({
            "success": True,
            "total": len(resultado.get('viagens_preparadas', [])),
            "dados": resultado.get('viagens_preparadas', [])
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
