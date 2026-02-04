
from flask import Blueprint, render_template, request, jsonify
from ..utils.logic import obter_status_prep
from ..utils.colaborador_utils import buscar_nome_colaborador_por_codigo
from ..utils.conferencia_status_prep import buscar_paletes_em_conferencia
    
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


# Novo endpoint: Viagens Pendentes com nome do colaborador
@status_prep_bp.route('/status-prep/pendentes', methods=['GET'])
def viagens_pendentes():
    data_inicial = request.args.get('dataInicial')
    data_final = request.args.get('dataFinal')
    nome_preparador = request.args.get('preparador', '').strip()
    if not data_inicial or not data_final:
        return jsonify({"success": False, "error": "Parâmetros dataInicial e dataFinal são obrigatórios"}), 400
    try:
        resultado = obter_status_prep(data_inicial, data_final, nome_preparador)
        if not resultado.get('success'):
            return jsonify({"success": False, "error": "Erro ao obter dados"}), 500
        viagens = resultado.get('viagens_pendentes', [])
        # Adiciona o nome do colaborador para cada item
        for v in viagens:
            codigo = v.get('prep', '').strip()
            v['nome'] = buscar_nome_colaborador_por_codigo(codigo) if codigo else ''
        return jsonify({
            "success": True,
            "total": len(viagens),
            "dados": viagens
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Novo endpoint: Paletes em Conferência
@status_prep_bp.route('/api/status-prep/conferencia', methods=['GET'])
def paletes_conferencia():
    """
    Retorna paletes preparados que ainda não estão 100% conferidos.
    """
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    nome_preparador = request.args.get('preparador', '').strip()
    
    print(f"[DEBUG API conferencia] Recebendo requisição: data_inicial={data_inicial}, data_final={data_final}, preparador='{nome_preparador}'")
    
    if not data_inicial or not data_final:
        print("[ERRO API conferencia] Parâmetros faltando")
        return jsonify({"success": False, "error": "Parâmetros data_inicial e data_final são obrigatórios"}), 400
    
    try:
        print(f"[DEBUG API conferencia] Chamando buscar_paletes_em_conferencia com preparador='{nome_preparador}'...")
        resultado = buscar_paletes_em_conferencia(data_inicial, data_final, nome_preparador)
        
        print(f"[DEBUG API conferencia] Resultado: success={resultado.get('success')}, total={resultado.get('total')}")
        
        if not resultado.get('success'):
            return jsonify(resultado), 500
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"[ERRO] Endpoint conferencia: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
