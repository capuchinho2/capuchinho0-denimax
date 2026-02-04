"""
Módulo para lógica de conferência na página Status Prep
"""

from .logic import obter_status_prep
from .conferencia_utils import analisar_palete, fazer_login
from .cache_conferencia import ler_cache_conferencia, salvar_cache_conferencia, atualizar_palete_no_cache


def buscar_paletes_em_conferencia(data_inicial, data_final, nome_preparador=''):
    """
    Busca paletes preparados e verifica quais estão em conferência (não 100% conferidos).
    
    Args:
        data_inicial: Data inicial para busca (formato: YYYY-MM-DD)
        data_final: Data final para busca (formato: YYYY-MM-DD)
        nome_preparador: Nome do preparador (opcional)
    
    Returns:
        dict: {
            "success": bool,
            "total": int,
            "paletes": [{"viagem": str, "palete": str, "status": str, "percentual": int}]
        }
    """
    try:
        print(f"[DEBUG conferencia_status_prep] Iniciando busca - data_inicial={data_inicial}, data_final={data_final}, preparador='{nome_preparador}'")
        
        # Buscar paletes preparados no período
        resultado = obter_status_prep(data_inicial, data_final, nome_preparador)
        
        if not resultado.get('success'):
            print("[ERRO conferencia_status_prep] Erro ao obter paletes preparados")
            return {"success": False, "error": "Erro ao obter paletes preparados"}
        
        viagens_preparadas = resultado.get('viagens_preparadas', [])
        print(f"[DEBUG conferencia_status_prep] Total de paletes preparados encontrados: {len(viagens_preparadas)}")
        
        # Debug: mostrar alguns exemplos
        if viagens_preparadas:
            print(f"[DEBUG conferencia_status_prep] Exemplos: {viagens_preparadas[:3]}")
        
        if not viagens_preparadas:
            print("[DEBUG conferencia_status_prep] Nenhum palete preparado encontrado para o filtro")
            return {
                "success": True,
                "total": 0,
                "paletes": []
            }
        
        # Fazer login uma vez
        print("[DEBUG conferencia_status_prep] Fazendo login...")
        if not fazer_login():
            print("[ERRO conferencia_status_prep] Falha no login")
            return {"success": False, "error": "Erro ao fazer login no sistema"}
        
        paletes_em_conferencia = []
        
        # Para cada palete preparado, verificar se está conferido
        for idx, item in enumerate(viagens_preparadas):
            viagem = item.get('viagem', '')
            palete = item.get('palete', '')
            prep = item.get('prep', '')
            
            if idx < 5:  # Mostrar apenas os primeiros 5 no log
                print(f"[DEBUG conferencia_status_prep] Processando {idx+1}/{len(viagens_preparadas)}: viagem={viagem}, palete={palete}, prep={prep}")
            elif idx == 5:
                print(f"[DEBUG conferencia_status_prep] ... (continuando processamento de {len(viagens_preparadas)} paletes)")
            
            if not viagem or not palete:
                continue
            
            # Analisar diretamente o palete específico (acessa viagem+palete no site)
            palete_info = analisar_palete(viagem, palete)
            
            if not palete_info:
                print(f"[AVISO conferencia_status_prep] Falha ao analisar palete {viagem}{palete}")
                continue
            
            percentual = palete_info.get('percentual', 0)
            status = palete_info.get('status', 'Pendente')
            nao_lancado = palete_info.get('nao_lancado', False)
            
            print(f"[DEBUG conferencia_status_prep] Palete {palete} - {percentual}% conferido, status={status}")
            
            # Se não está 100% conferido OU não foi lançado, adicionar à lista
            if percentual < 100 or nao_lancado:
                paletes_em_conferencia.append({
                    'viagem': viagem,
                    'palete': palete,
                    'status': status,
                    'percentual': percentual,
                    'prep': prep
                })
        
        print(f"[DEBUG conferencia_status_prep] Total em conferência: {len(paletes_em_conferencia)}")
        
        return {
            "success": True,
            "total": len(paletes_em_conferencia),
            "paletes": paletes_em_conferencia
        }
        
    except Exception as e:
        print(f"[ERRO] buscar_paletes_em_conferencia: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def buscar_todos_paletes_conferencia(data_inicial, data_final, nome_preparador=''):
    """
    Busca TODOS os paletes (preparados + incompletos) e verifica o status de conferência.
    Usa cache inteligente: paletes 100% conferidos não são revalidados.
    
    Args:
        data_inicial: Data inicial para busca (formato: YYYY-MM-DD)
        data_final: Data final para busca (formato: YYYY-MM-DD)
        nome_preparador: Nome do preparador (opcional)
    
    Returns:
        dict: {
            "success": bool,
            "total": int,
            "paletes": [{"viagem": str, "palete": str, "prep": str, "status": str, "percentual": int}]
        }
    """
    try:
        print(f"[DEBUG buscar_todos_paletes_conferencia] Iniciando - data_inicial={data_inicial}, data_final={data_final}, preparador='{nome_preparador}'")
        
        # Tentar ler cache primeiro
        cache_data = ler_cache_conferencia(data_inicial, data_final, nome_preparador)
        
        # Buscar todos os paletes (preparados + incompletos)
        resultado = obter_status_prep(data_inicial, data_final, nome_preparador)
        
        if not resultado.get('success'):
            print("[ERRO buscar_todos_paletes_conferencia] Erro ao obter dados")
            return {"success": False, "error": "Erro ao obter dados"}
        
        # Combinar preparados e incompletos
        viagens_preparadas = resultado.get('viagens_preparadas', [])
        viagens_pendentes = resultado.get('viagens_pendentes', [])
        
        todas_viagens = viagens_preparadas + viagens_pendentes
        print(f"[DEBUG buscar_todos_paletes_conferencia] Total: {len(todas_viagens)} paletes (preparados={len(viagens_preparadas)}, pendentes={len(viagens_pendentes)})")
        
        if not todas_viagens:
            return {
                "success": True,
                "total": 0,
                "paletes": []
            }
        
        # Criar dicionário de cache para acesso rápido
        cache_dict = {}
        if cache_data and 'paletes' in cache_data:
            print(f"[DEBUG buscar_todos_paletes_conferencia] Cache encontrado com {len(cache_data['paletes'])} paletes")
            for p in cache_data['paletes']:
                key = f"{p['viagem']}{p['palete']}"
                cache_dict[key] = p
        else:
            print("[DEBUG buscar_todos_paletes_conferencia] Nenhum cache encontrado, fazendo busca completa")
        
        # Fazer login uma vez
        print("[DEBUG buscar_todos_paletes_conferencia] Fazendo login...")
        if not fazer_login():
            print("[ERRO buscar_todos_paletes_conferencia] Falha no login")
            return {"success": False, "error": "Erro ao fazer login no sistema"}
        
        paletes_resultado = []
        paletes_atualizados = 0
        paletes_do_cache = 0
        
        # Para cada palete, verificar status de conferência
        for idx, item in enumerate(todas_viagens):
            viagem = item.get('viagem', '')
            palete = item.get('palete', '')
            prep = item.get('prep', '')
            
            if idx < 5:
                print(f"[DEBUG buscar_todos_paletes_conferencia] Processando {idx+1}/{len(todas_viagens)}: viagem={viagem}, palete={palete}, prep={prep}")
            elif idx == 5:
                print(f"[DEBUG buscar_todos_paletes_conferencia] ... (continuando {len(todas_viagens)} paletes)")
            
            if not viagem or not palete:
                continue
            
            # Verificar se existe no cache
            cache_key = f"{viagem}{palete}"
            cache_palete = cache_dict.get(cache_key)
            
            # Se tem cache E está 100% conferido, usar cache sem consultar
            if cache_palete and cache_palete.get('percentual') == 100:
                print(f"[DEBUG buscar_todos_paletes_conferencia] ✓ Palete {viagem}{palete} 100% conferido, usando cache")
                paletes_resultado.append(cache_palete)
                paletes_do_cache += 1
                continue
            
            # Se não tem cache OU não está 100%, consultar
            print(f"[DEBUG buscar_todos_paletes_conferencia] → Palete {viagem}{palete} precisa ser consultado")
            
            # Analisar palete
            palete_info = analisar_palete(viagem, palete)
            
            if not palete_info:
                print(f"[AVISO buscar_todos_paletes_conferencia] Falha ao analisar {viagem}{palete}")
                # Se falhou, adicionar como "Não verificado"
                paletes_resultado.append({
                    'viagem': viagem,
                    'palete': palete,
                    'prep': prep,
                    'status': 'Não verificado',
                    'percentual': 0
                })
                continue
            
            percentual = palete_info.get('percentual', 0)
            status = palete_info.get('status', 'Pendente')
            
            # Se não está 100% conferido, forçar atualização do cache para garantir dados atuais
            if percentual < 100:
                print(f"[DEBUG buscar_todos_paletes_conferencia] Palete {viagem}{palete} não está 100%, forçando atualização...")
                palete_info_atualizado = analisar_palete(viagem, palete, forcar_atualizacao=True)
                if palete_info_atualizado:
                    palete_info = palete_info_atualizado
                    percentual = palete_info.get('percentual', 0)
                    status = palete_info.get('status', 'Pendente')
            
            paletes_resultado.append({
                'viagem': viagem,
                'palete': palete,
                'prep': prep,
                'status': status,
                'percentual': percentual
            })
            paletes_atualizados += 1
        
        print(f"[DEBUG buscar_todos_paletes_conferencia] Processamento concluído:")
        print(f"  - Total: {len(paletes_resultado)} paletes")
        print(f"  - Do cache (100%): {paletes_do_cache}")
        print(f"  - Consultados: {paletes_atualizados}")
        
        # Salvar/atualizar cache com os novos dados
        salvar_cache_conferencia(data_inicial, data_final, nome_preparador, paletes_resultado)
        
        return {
            "success": True,
            "total": len(paletes_resultado),
            "paletes": paletes_resultado,
            "cache_stats": {
                "do_cache": paletes_do_cache,
                "consultados": paletes_atualizados
            }
        }
        
    except Exception as e:
        print(f"[ERRO] buscar_todos_paletes_conferencia: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
