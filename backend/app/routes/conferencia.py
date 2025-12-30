from flask import Blueprint, render_template, jsonify, request
from app.utils.conferencia_utils import buscar_viagem_completa, forcar_atualizacao_site, acessar_suporte_com_cache
from bs4 import BeautifulSoup

conferencia_bp = Blueprint('conferencia', __name__)

@conferencia_bp.route('/conferencia')
def conferencia():
    return render_template('conferencia.html')

@conferencia_bp.route('/api/conferencia/viagem')
def api_buscar_viagem():
    """API para buscar dados de uma viagem específica."""
    viagem = request.args.get('viagem')
    
    if not viagem:
        return jsonify({"success": False, "error": "Número da viagem não fornecido"}), 400
    
    try:
        resultado = buscar_viagem_completa(int(viagem))
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@conferencia_bp.route('/api/conferencia/detalhar', methods=['POST'])
def api_detalhar_palete():
    """API para detalhar um palete específico."""
    data = request.get_json()
    viagem = data.get('viagem')
    palete = data.get('palete')
    
    if not viagem or not palete:
        return jsonify({"success": False, "error": "Dados inválidos"}), 400
    
    try:
        suporte_id = f"{viagem}{palete}"
        html = acessar_suporte_com_cache(suporte_id)
        
        if not html:
            return jsonify({"success": False, "error": "Erro ao acessar suporte"})
        
        soup = BeautifulSoup(html, "html.parser")
        tabela = soup.find("table")
        
        if not tabela:
            return jsonify({"success": False, "error": "Tabela não encontrada"})
        
        tbody = tabela.find("tbody")
        if not tbody:
            return jsonify({"success": False, "error": "Tbody não encontrado"})
        
        linhas = tbody.find_all("tr")
        itens = []
        faltam_bipar = 0
        faltam_conferir = 0
        linhas_pendentes = 0
        
        for row in linhas:
            row_class = row.get("class") or []
            if "gray" in row_class:
                continue
            
            linhas_pendentes += 1
            cols = row.find_all("td")
            codigo = cols[0].text.strip() if len(cols) > 0 else ""
            descricao = cols[2].text.strip() if len(cols) > 2 else ""
            qtde = cols[5].text.strip() if len(cols) > 5 else ""
            
            if "red" in row_class:
                status = "❌ FALTA BIPAR"
                faltam_bipar += 1
            elif "white" in row_class:
                status = "❌ FALTA CONFERIR"
                faltam_conferir += 1
            else:
                status = ""
            
            itens.append({
                'codigo': codigo,
                'descricao': descricao,
                'qtde': qtde,
                'status': status
            })
        
        if linhas_pendentes == 0:
            return jsonify({
                "success": True,
                "mensagem": "✅ Todas as linhas deste palete já foram conferidas!"
            })
        
        return jsonify({
            "success": True,
            "itens": itens,
            "faltam_bipar": faltam_bipar,
            "faltam_conferir": faltam_conferir
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@conferencia_bp.route('/api/conferencia/atualizar-palete', methods=['POST'])
def api_atualizar_palete():
    """API para forçar nova busca do palete e atualizar cache."""
    data = request.get_json()
    viagem = data.get('viagem')
    palete = data.get('palete')
    
    if not viagem or not palete:
        return jsonify({"success": False, "error": "Dados inválidos"}), 400
    
    try:
        # Força nova busca ignorando cache (forcar_atualizacao=True)
        # Isso vai buscar do servidor e atualizar o cache automaticamente
        suporte_id = f"{viagem}{palete}"
        html = acessar_suporte_com_cache(suporte_id, forcar_atualizacao=True)
        
        if html:
            return jsonify({"success": True, "message": "Palete atualizado com sucesso!"})
        else:
            return jsonify({"success": False, "error": "Erro ao atualizar palete"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
