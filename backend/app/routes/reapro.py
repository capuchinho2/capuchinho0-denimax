from flask import Blueprint, render_template, request, jsonify, send_file
import os
import sys
from datetime import datetime
import pandas as pd

# Adicionar o diretório backend ao path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
backend_dir = os.path.join(root_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Importar dados das vagas do Excel
try:
    import vagas_data as vd_module
    vagas_db = vd_module.vagas_data.copy()
    print(f"✅ {len(vagas_db)} vagas carregadas do Excel")
except Exception as e:
    print(f"⚠️ Erro ao carregar vagas_data: {e}")
    vagas_db = []

# Importar queries do AS400
try:
    import reapro_queries
    buscar_paletes_disponiveis = reapro_queries.buscar_paletes_disponiveis
    buscar_reapro_pendente = reapro_queries.buscar_reapro_pendente
    exportar_para_excel = reapro_queries.exportar_para_excel
    testar_conexao = reapro_queries.testar_conexao
    REAPRO_DISPONIVEL = True
except Exception as e:
    print(f"⚠️ Módulo reapro_queries não disponível: {e}")
    REAPRO_DISPONIVEL = False
    buscar_paletes_disponiveis = None
    exportar_para_excel = None

reapro_bp = Blueprint('reapro', __name__)

# Formato: { id, rua, vaga, nivel (sempre 1), produto, quantidade }


@reapro_bp.route('/reapro')
def reapro():
    """Página de Estoque Picking - Controle de Vagas"""
    return render_template('reapro.html')


@reapro_bp.route('/reapro-pendente')
def reapro_pendente():
    """Página de Reapro Pendente - Lista de Paletes AS400"""
    return render_template('estoque_picking.html')


@reapro_bp.route('/reapro/listar-pendentes', methods=['GET'])
def listar_paletes_pendentes():
    """Buscar todos os paletes pendentes de reaproveitamento (ETAPAL='20')"""
    try:
        if not REAPRO_DISPONIVEL:
            return jsonify({
                "success": False,
                "error": "Módulo AS400 não disponível"
            }), 500
        
        # Buscar todos os paletes pendentes sem filtro de produto
        limit = request.args.get('limit', 500, type=int)  # Limite padrão: 500
        
        paletes = buscar_reapro_pendente(codpro=None, limit=limit)
        
        return jsonify({
            "success": True,
            "total": len(paletes),
            "dados": paletes
        })
    except Exception as e:
        print(f"❌ Erro ao buscar paletes pendentes: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/exportar-pendentes', methods=['POST'])
def exportar_pendentes_excel():
    """Exportar lista de paletes pendentes para Excel"""
    if not REAPRO_DISPONIVEL:
        return jsonify({
            "success": False,
            "error": "Módulo de exportação não disponível"
        }), 503
    
    try:
        dados = request.get_json()
        paletes = dados.get('paletes', [])
        
        if not paletes:
            return jsonify({
                "success": False,
                "error": "Nenhum palete para exportar"
            }), 400
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f'reapro_pendentes_{timestamp}.xlsx'
        caminho_arquivo = os.path.join(backend_dir, nome_arquivo)
        
        # Criar DataFrame com os dados
        df = pd.DataFrame(paletes)
        
        # Ordenar colunas
        ordem_colunas = ['ENDERECO', 'CODPRO', 'DS1PRO', 'CODLOT', 'ONDA', 'CXS_ESTO']
        colunas_existentes = [col for col in ordem_colunas if col in df.columns]
        df = df[colunas_existentes]
        
        # Converter código do produto removendo zeros à esquerda
        if 'CODPRO' in df.columns:
            df['CODPRO'] = df['CODPRO'].apply(lambda x: str(x).lstrip('0') if pd.notna(x) and str(x).strip() else x)
        
        # Renomear colunas para português
        df = df.rename(columns={
            'ENDERECO': 'Endereço',
            'CODPRO': 'Código',
            'DS1PRO': 'Descrição',
            'CODLOT': 'Lote',
            'ONDA': 'Onda',
            'CXS_ESTO': 'Cxs'
        })
        
        # Criar arquivo Excel com formatação
        with pd.ExcelWriter(caminho_arquivo, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Paletes Pendentes', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Paletes Pendentes']
            
            # Formatos
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4A90E2',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            # Formato para células de dados com bordas
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            # Aplicar formato ao cabeçalho
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Aplicar bordas em todas as células de dados
            for row_num in range(1, len(df) + 1):
                for col_num in range(len(df.columns)):
                    cell_value = df.iloc[row_num - 1, col_num]
                    worksheet.write(row_num, col_num, cell_value, cell_format)
            
            # Ajustar largura das colunas
            worksheet.set_column('A:A', 15)  # Endereço
            worksheet.set_column('B:B', 9)  # Código
            worksheet.set_column('C:C', 40)  # Descrição
            worksheet.set_column('D:D', 10)  # Lote
            worksheet.set_column('E:E', 9)  # Onda
            worksheet.set_column('F:F', 6)  # Cxs
            
            # Adicionar autofiltro
            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
        
        if os.path.exists(caminho_arquivo):
            return send_file(
                caminho_arquivo,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=nome_arquivo
            )
        else:
            return jsonify({
                "success": False,
                "error": "Erro ao gerar arquivo Excel"
            }), 500
        
    except Exception as e:
        print(f"❌ Erro ao exportar Excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/vagas', methods=['GET'])
def listar_vagas():
    """Listar todas as vagas"""
    try:
        # Usar vagas_db global
        global vagas_db
        
        # Se vazio, tentar recarregar
        if not vagas_db or len(vagas_db) == 0:
            try:
                import vagas_data as vd_module
                vd_module_reload = __import__('vagas_data')
                vagas_db = vd_module_reload.vagas_data.copy()
                print(f"🔄 Vagas recarregadas: {len(vagas_db)}")
            except Exception as e:
                print(f"⚠️ Erro ao recarregar: {e}")
        
        rua_filtro = request.args.get('rua', type=int)
        status_filtro = request.args.get('status')  # 'vazio' ou 'cheio'
        
        print(f"🔍 DEBUG: vagas_db tem {len(vagas_db)} vagas")
        
        vagas = vagas_db.copy() if vagas_db else []
        
        # Aplicar filtros
        if rua_filtro:
            vagas = [v for v in vagas if v['rua'] == rua_filtro]
        
        if status_filtro:
            if status_filtro == 'vazio':
                vagas = [v for v in vagas if v['quantidade'] == 0]
            elif status_filtro == 'cheio':
                vagas = [v for v in vagas if v['quantidade'] > 0]
        
        return jsonify({
            "success": True,
            "total": len(vagas),
            "dados": vagas
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/vagas', methods=['POST'])
def criar_vaga():
    """Criar uma nova vaga formato (Rua-Vaga)"""
    try:
        dados = request.get_json()
        
        # Validações
        if 'rua' not in dados or 'vaga' not in dados:
            return jsonify({
                "success": False,
                "error": "Campos 'rua' e 'vaga' são obrigatórios"
            }), 400
        
        rua = int(dados['rua'])
        vaga = int(dados['vaga'])
        
        # Verificar se já existe
        existente = next((v for v in vagas_db if v['rua'] == rua and v['vaga'] == vaga), None)
        if existente:
            return jsonify({
                "success": False,
                "error": f"Vaga {rua}-{vaga} já existe"
            }), 400
        
        # Criar nova vaga
        novo_id = max([v['id'] for v in vagas_db], default=0) + 1
        
        nova_vaga = {
            "id": novo_id,
            "rua": rua,
            "vaga": vaga,
            "nivel": 1,  # Sempre 1
            "produto": dados.get('produto', '').strip(),
            "quantidade": int(dados.get('quantidade', 0))
        }
        
        vagas_db.append(nova_vaga)
        
        return jsonify({
            "success": True,
            "mensagem": f"Vaga {rua}-{vaga} criada com sucesso",
            "vaga": nova_vaga
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/vagas/<int:vaga_id>', methods=['PUT'])
def atualizar_vaga(vaga_id):
    """Atualizar uma vaga existente"""
    try:
        vaga = next((v for v in vagas_db if v['id'] == vaga_id), None)
        if not vaga:
            return jsonify({
                "success": False,
                "error": "Vaga não encontrada"
            }), 404
        
        dados = request.get_json()
        
        # Verificar duplicidade se mudar rua/vaga
        if 'rua' in dados or 'vaga' in dados:
            nova_rua = int(dados.get('rua', vaga['rua']))
            nova_vaga = int(dados.get('vaga', vaga['vaga']))
            
            duplicada = next((v for v in vagas_db 
                            if v['id'] != vaga_id 
                            and v['rua'] == nova_rua 
                            and v['vaga'] == nova_vaga), None)
            if duplicada:
                return jsonify({
                    "success": False,
                    "error": f"Vaga {nova_rua}-{nova_vaga} já existe"
                }), 400
            
            vaga['rua'] = nova_rua
            vaga['vaga'] = nova_vaga
        
        # Atualizar outros campos
        if 'produto' in dados:
            vaga['produto'] = dados['produto'].strip()
        if 'quantidade' in dados:
            vaga['quantidade'] = int(dados['quantidade'])
        
        return jsonify({
            "success": True,
            "mensagem": "Vaga atualizada com sucesso",
            "vaga": vaga
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/vagas/<int:vaga_id>', methods=['DELETE'])
def excluir_vaga(vaga_id):
    """Excluir uma vaga"""
    try:
        global vagas_db
        
        vaga = next((v for v in vagas_db if v['id'] == vaga_id), None)
        if not vaga:
            return jsonify({
                "success": False,
                "error": "Vaga não encontrada"
            }), 404
        
        vagas_db = [v for v in vagas_db if v['id'] != vaga_id]
        
        return jsonify({
            "success": True,
            "mensagem": f"Vaga {vaga['rua']}-{vaga['vaga']} excluída com sucesso"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Obter estatísticas das vagas"""
    try:
        total = len(vagas_db)
        vazias = sum(1 for v in vagas_db if v['quantidade'] == 0)
        cheias = total - vazias
        
        taxa_ocupacao = (cheias / total * 100) if total > 0 else 0
        
        return jsonify({
            "success": True,
            "estatisticas": {
                "total": total,
                "vazias": vazias,
                "cheias": cheias,
                "taxa_ocupacao": round(taxa_ocupacao, 1)
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/importar-excel', methods=['POST'])
def importar_excel():
    """Importar vagas de arquivo Excel (formato Rua-Vaga)"""
    try:
        # TODO: Implementar lógica de importação do Excel
        # Esperado: arquivo com colunas tipo "VAGAS (12-2)" onde 12=rua, 2=vaga
        
        return jsonify({
            "success": False,
            "error": "Funcionalidade em desenvolvimento"
        }), 501
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== NOVAS ROTAS PARA CONSULTA AS400 ==========

@reapro_bp.route('/reapro/consultar-paletes', methods=['GET'])
def consultar_paletes():
    """Consultar paletes disponíveis no AS400 para preenchimento de vagas vazias"""
    if not REAPRO_DISPONIVEL:
        return jsonify({
            "success": False,
            "error": "Módulo de consulta AS400 não disponível"
        }), 503
    
    try:
        # Pegar todas as vagas vazias
        vagas_vazias = [v for v in vagas_db if v['quantidade'] == 0 and v['produto']]
        
        if not vagas_vazias:
            return jsonify({
                "success": True,
                "total": 0,
                "dados": [],
                "mensagem": "Nenhuma vaga vazia com produto fixo encontrada"
            })
        
        # Agrupar vagas vazias por produto para buscar múltiplos paletes de uma vez
        vagas_por_produto = {}
        for vaga in vagas_vazias:
            produto = vaga['produto']
            if produto not in vagas_por_produto:
                vagas_por_produto[produto] = []
            vagas_por_produto[produto].append(vaga)
        
        resultados = []
        paletes_usados = set()  # Controlar paletes já atribuídos
        
        # Para cada produto, buscar paletes suficientes para todas as vagas
        for produto, vagas in vagas_por_produto.items():
            # Extrair apenas o número do código (remover A-, B-, C-)
            codigo_numerico = produto.split('-')[1] if '-' in produto else produto
            
            qtd_vagas = len(vagas)
            print(f"🔍 Produto {produto}: {qtd_vagas} vagas vazias")
            
            # Buscar paletes suficientes (limitar a 20 para não sobrecarregar)
            paletes = buscar_reapro_pendente(codigo_numerico, limit=min(qtd_vagas * 2, 20))
            
            # Filtrar paletes que já foram usados
            paletes_disponiveis = [
                p for p in paletes 
                if p.get('ENDERECO', '') not in paletes_usados
            ]
            
            print(f"   Encontrados {len(paletes)} paletes, {len(paletes_disponiveis)} disponíveis após filtro")
            
            # Atribuir um palete diferente para cada vaga
            for i, vaga in enumerate(vagas):
                if i < len(paletes_disponiveis):
                    # Tem palete disponível para esta vaga
                    palete = paletes_disponiveis[i]
                    endereco = palete.get('ENDERECO', '')
                    paletes_usados.add(endereco)  # Marcar como usado
                    
                    resultados.append({
                        'ENDERECO_PALETE': endereco,
                        'DESCRICAO': palete.get('DS1PRO', ''),
                        'PRODUTO_VAGA': vaga['produto'],
                        'CODLOT': palete.get('CODLOT', ''),
                        'ONDA': palete.get('ONDA', ''),
                        'QTD_CAIXAS': palete.get('CXS_ESTO', ''),
                        'DISPONIBILIDADE': '✅ DISPONÍVEL',
                        'VAGA PICKING': f"{vaga['rua']}-{vaga['vaga']}"
                    })
                    print(f"   ✅ Vaga {vaga['rua']}-{vaga['vaga']} → Palete {endereco}")
                else:
                    # Não tem palete disponível para esta vaga
                    resultados.append({
                        'ENDERECO_PALETE': 'N/A',
                        'DESCRICAO': 'N/A',
                        'PRODUTO_VAGA': vaga['produto'],
                        'CODLOT': 'N/A',
                        'ONDA': 'N/A',
                        'QTD_CAIXAS': 'N/A',
                        'DISPONIBILIDADE': '❌ SEM ESTOQUE',
                        'VAGA PICKING': f"{vaga['rua']}-{vaga['vaga']}"
                    })
                    print(f"   ❌ Vaga {vaga['rua']}-{vaga['vaga']} → SEM ESTOQUE")
        
        return jsonify({
            "success": True,
            "total": len(resultados),
            "vagas_vazias_analisadas": len(vagas_vazias),
            "dados": resultados
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/exportar-excel', methods=['POST'])
def exportar_paletes_excel():
    """Exportar dados de paletes para Excel"""
    if not REAPRO_DISPONIVEL:
        return jsonify({
            "success": False,
            "error": "Módulo de exportação não disponível"
        }), 503
    
    try:
        dados = request.get_json()
        paletes = dados.get('paletes', [])
        
        if not paletes:
            return jsonify({
                "success": False,
                "error": "Nenhum palete para exportar"
            }), 400
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f'reapro_paletes_{timestamp}.xlsx'
        
        # Usar backend_dir que já está definido no início do arquivo
        caminho_arquivo = os.path.join(backend_dir, nome_arquivo)
        
        # Exportar para Excel
        arquivo_gerado = exportar_para_excel(paletes, caminho_arquivo)
        
        if arquivo_gerado and os.path.exists(arquivo_gerado):
            return send_file(
                arquivo_gerado,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=nome_arquivo
            )
        else:
            return jsonify({
                "success": False,
                "error": "Erro ao gerar arquivo Excel"
            }), 500
        
    except Exception as e:
        print(f"❌ Erro ao exportar Excel: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/testar-conexao', methods=['GET'])
def testar_conexao_as400():
    """Testar conexão com AS400"""
    if not REAPRO_DISPONIVEL:
        return jsonify({
            "success": False,
            "error": "Módulo de conexão não disponível"
        }), 503
    
    try:
        resultado = testar_conexao()
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@reapro_bp.route('/reapro/preencher-todas', methods=['POST'])
def preencher_todas_vagas():
    """Preencher todas as vagas vazias (quantidade = 1)"""
    try:
        global vagas_db
        
        # Contar vagas vazias
        vagas_vazias = [v for v in vagas_db if v['quantidade'] == 0]
        total_vazias = len(vagas_vazias)
        
        if total_vazias == 0:
            return jsonify({
                "success": True,
                "mensagem": "Todas as vagas já estão cheias!",
                "total_preenchidas": 0
            })
        
        # Preencher todas as vagas vazias
        for vaga in vagas_vazias:
            vaga['quantidade'] = 1
            # Se a vaga não tem produto, adiciona um padrão
            if not vaga['produto'] or vaga['produto'].strip() == '':
                vaga['produto'] = f"PROD-{vaga['rua']}{vaga['vaga']}"
        
        return jsonify({
            "success": True,
            "mensagem": f"{total_vazias} vagas preenchidas com sucesso!",
            "total_preenchidas": total_vazias
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
