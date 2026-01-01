
from flask import Blueprint, request, jsonify, render_template
rastreabilidade_bp = Blueprint('rastreabilidade', __name__)

# Endpoint para inserir várias viagens de uma vez
@rastreabilidade_bp.route('/api/viagens/lote', methods=['POST'])
def api_inserir_viagens_lote():
    data = request.get_json()
    viagens = data.get('viagens', [])
    inseridas = 0
    erros = []
    for viagem in viagens:
        try:
            inserir_viagem(viagem)
            inseridas += 1
        except Exception as e:
            erros.append(str(e))
    msg = f'{inseridas} viagens inseridas com sucesso.'
    if erros:
        msg += f' {len(erros)} não inseridas (duplicadas ou erro).'
    return jsonify({'message': msg, 'erros': erros})

# Endpoint para excluir todas as viagens e limpar cache
import shutil
@rastreabilidade_bp.route('/api/viagens/todas', methods=['DELETE'])
def api_excluir_todas_viagens():
    try:
        from ..utils.viagem_utils import get_sqlite_connection
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM viagens')
        conn.commit()
        cursor.close()
        conn.close()
        # Limpa todos os arquivos de cache em cash_plts
        from pathlib import Path
        cache_dir = Path(__file__).parent.parent.parent / 'cash_plts'
        if cache_dir.exists():
            for f in cache_dir.glob('*.json'):
                f.unlink()
        return jsonify({'message': 'Todas as viagens e caches foram excluídos!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
from ..utils.viagem_utils import inserir_viagem, listar_viagens, atualizar_status_viagem, excluir_viagem, get_sqlite_connection
from ..utils.logic import buscar_conferencia_viagem
# Adiciona utilitário de cache
from ..utils.cache_utils import salvar_cache_palete, ler_cache_palete
import pyodbc
# Função utilitária para verificar se a viagem está preparada
def viagem_esta_preparada(viagem):
    conn_str = (
        "DRIVER={iSeries Access ODBC Driver};"
        "SYSTEM=FGE5006CDP;"
        "UID=CDP174176G;"
        "PWD=CDP1753;"
    )
    sql = f'''
        SELECT (CASE DANALLCDP.ONDAITM.TYPSUP WHEN 1 THEN 'HET' ELSE 'HOM' END) AS TIPO,
               CAST(SUM(DANALLCDP.ONDAITM.QTDLIDA) AS FLOAT) / NULLIF(CAST(SUM(DANALLCDP.ONDAITM.RCAIXAS) AS FLOAT),0) AS PERC_PREP
        FROM DANALLCDP.ONDAITM
        LEFT JOIN DANALLCDP.ONDADET ON DANALLCDP.ONDADET.VIAGEM||DANALLCDP.ONDADET.PALETE = DANALLCDP.ONDAITM.VIAGEM||DANALLCDP.ONDAITM.PALETE
        WHERE DANALLCDP.ONDAITM.VIAGEM='{viagem}'
        GROUP BY DANALLCDP.ONDAITM.VIAGEM, DANALLCDP.ONDAITM.PALETE, DANALLCDP.ONDAITM.TYPSUP, DANALLCDP.ONDADET.MIS_DONE
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        rows = []
        cursor.execute(sql)
        for row in cursor.fetchall():
            tipo = row[0]
            perc_prep = float(row[1] or 0)
            if tipo == 'HET':
                rows.append(perc_prep)
        cursor.close()
        conn.close()
        return bool(rows) and all(abs(perc - 1.0) < 0.0001 for perc in rows)
    except Exception as e:
        print(f"Erro ao verificar preparação: {e}")
        return False
# ...existing code...
# Rota para excluir viagem
@rastreabilidade_bp.route('/api/viagens/<int:viagem_id>', methods=['DELETE'])
def api_excluir_viagem(viagem_id):
    from ..utils.cache_utils import get_cache_path
    try:
        excluir_viagem(viagem_id)
        # Remove o cache se existir
        cache_path = get_cache_path(viagem_id)
        if cache_path.exists():
            cache_path.unlink()
        return jsonify({'message': 'Viagem excluída com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para exibir a página HTML
@rastreabilidade_bp.route('/rastreabilidade')
def rastreabilidade_page():
    return render_template('rastreabilidade.html')

# Endpoint de orquestração de status de rastreabilidade
@rastreabilidade_bp.route('/api/rastreabilidade', methods=['GET'])
def api_rastreabilidade():
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, viagem, preparada, conferida, expedida, data_criacao FROM viagens ORDER BY id DESC')
        viagens = cursor.fetchall()
        resultado = []
        for v in viagens:
            viagem_id, viagem, preparada, conferida, expedida, data_criacao = v
            print(f"Processando viagem: {viagem_id} | {viagem}")
            if not viagem or not str(viagem).strip():
                print(f"Ignorando viagem inválida: {viagem_id} | {viagem}")
                continue
            # Tenta ler do cache incremental
            cache_data = ler_cache_palete(viagem_id) or {}
            status = {
                'id': viagem_id,
                'viagem': viagem,
                'preparada': cache_data.get('preparada', bool(preparada)),
                'conferida': cache_data.get('conferida', bool(conferida)),
                'expedida': cache_data.get('expedida', bool(expedida)),
                'data_criacao': str(data_criacao),
                'cache': False
            }
            # Preenche expedida_html do cache, se existir
            if 'expedida_html' in cache_data:
                status['expedida_html'] = cache_data['expedida_html']
            atualizou = False
            # Só consulta o backend para status "Não"
            try:
                if not status['preparada']:
                    preparada_atual = viagem_esta_preparada(viagem)
                    status['preparada'] = preparada_atual
                    if preparada_atual and not preparada:
                        cursor.execute('UPDATE viagens SET preparada = 1 WHERE id = ?', (viagem_id,))
                        conn.commit()
                    atualizou = True
                if not status['conferida']:
                    from ..utils.conferencia_utils import buscar_viagem_completa
                    try:
                        conf_result = buscar_viagem_completa(viagem)
                        if conf_result.get('success'):
                            total = conf_result.get('total_paletes', 0)
                            completos = conf_result.get('completos', 0)
                            status['conferida'] = (total > 0 and completos == total)
                            if status['conferida'] and not conferida:
                                cursor.execute('UPDATE viagens SET conferida = 1 WHERE id = ?', (viagem_id,))
                                conn.commit()
                        atualizou = True
                    except Exception as e:
                        print(f"Erro ao verificar conferência: {e}")
                if not status['expedida']:
                    try:
                        conn_str = (
                            "DRIVER={iSeries Access ODBC Driver};"
                            "SYSTEM=FGE5006CDP;"
                            "UID=CDP174176G;"
                             "PWD=CDP1753;"
                        )
                        sql = f'''
                            SELECT (CASE DANALLCDP.ONDAITM.TYPSUP WHEN 1 THEN 'HET' ELSE 'HOM' END) AS TIPO,
                                   DANALLCDP.ONDADET.MIS_DONE
                            FROM DANALLCDP.ONDAITM
                            LEFT JOIN DANALLCDP.ONDADET ON DANALLCDP.ONDADET.VIAGEM||DANALLCDP.ONDADET.PALETE = DANALLCDP.ONDAITM.VIAGEM||DANALLCDP.ONDAITM.PALETE
                            WHERE DANALLCDP.ONDAITM.VIAGEM='{viagem}'
                        '''
                        conn2 = pyodbc.connect(conn_str)
                        cursor2 = conn2.cursor()
                        rows = cursor2.fetchall() if cursor2.execute(sql) is None else cursor2.fetchall()
                        # Robustez: validação e nomes claros
                        # Considera tanto HET quanto HOM
                        paletes_validos = [row for row in rows if row[0] in ('HET', 'HOM')]
                        total_paletes = len(paletes_validos)
                        paletes_bipados = [row for row in paletes_validos if row[1] == 'Y']
                        total_bipados = len(paletes_bipados)

                        # Condições explícitas  
                        todos_bipados = total_paletes > 0 and total_bipados == total_paletes
                        pelo_menos_um_bipado = total_bipados > 0 and total_bipados < total_paletes
                        nenhum_bipado = total_bipados == 0

                        # Garante que o HTML sempre será preenchido
                        if todos_bipados:
                            status['expedida_html'] = 'Sim'
                        elif pelo_menos_um_bipado:
                            status['expedida_html'] = 'Em preparação'
                        elif nenhum_bipado:
                            status['expedida_html'] = 'Não'
                        else:
                            # Caso raro: dados inconsistentes
                            status['expedida_html'] = 'Indefinido'
                        status['expedida'] = expedida
                        if expedida and not expedida:
                            cursor.execute('UPDATE viagens SET expedida = 1 WHERE id = ?', (viagem_id,))
                            conn.commit()
                        cursor2.close()
                        conn2.close()
                        atualizou = True
                    except Exception as e:
                        print(f"Erro ao verificar expedição: {e}")
            except Exception as e:
                print(f"Erro ao processar viagem {viagem_id} | {viagem}: {e}")
                continue
            # Salva sempre o status parcial/atualizado no cache
            salvar_cache_palete(viagem_id, status)
            # Se todos status forem True, marca como cache completo
            if status['preparada'] and status['conferida'] and status['expedida']:
                status['cache'] = True
            resultado.append(status)
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'dados': resultado})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'dados': []}), 500

@rastreabilidade_bp.route('/api/viagens', methods=['POST'])
def api_inserir_viagem():
    data = request.get_json()
    viagem = data.get('viagem')
    if not viagem:
        return jsonify({'error': 'Campo "viagem" é obrigatório.'}), 400
    try:
        inserir_viagem(viagem)
        return jsonify({'message': 'Viagem inserida com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rastreabilidade_bp.route('/api/viagens', methods=['GET'])
def api_listar_viagens():
    viagens = listar_viagens()
    viagens_list = []
    for v in viagens:
        viagens_list.append({
            'id': v[0],
            'viagem': v[1],
            'preparada': v[2],
            'conferida': v[3],
            'expedida': v[4],
            'data_criacao': str(v[5])
        })
    return jsonify(viagens_list)

@rastreabilidade_bp.route('/api/viagens/<int:viagem_id>/<status>', methods=['PATCH'])
def api_atualizar_status(viagem_id, status):
    if status not in ['preparada', 'conferida', 'expedida']:
        return jsonify({'error': 'Status inválido.'}), 400
    try:
        atualizar_status_viagem(viagem_id, status)
        return jsonify({'message': f'Status {status} atualizado!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


