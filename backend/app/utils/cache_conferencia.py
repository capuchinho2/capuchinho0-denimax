"""
Módulo para gerenciar cache de conferência por período.
Otimiza consultas guardando status de paletes já conferidos 100%.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta

# Diretório de cache
CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'cache_conferencia_filtro'
)

# Tempo de validade do cache (em horas)
CACHE_VALIDADE_HORAS = 48


def _get_cache_filename(data_inicial, data_final, preparador=''):
    """
    Gera nome do arquivo de cache baseado nos filtros.
    
    Args:
        data_inicial: Data inicial (YYYY-MM-DD)
        data_final: Data final (YYYY-MM-DD)
        preparador: Nome do preparador (opcional)
    
    Returns:
        str: Nome do arquivo de cache
    """
    # Criar string única com os filtros
    filtro_str = f"{data_inicial}_{data_final}_{preparador}"
    
    # Gerar hash MD5
    hash_md5 = hashlib.md5(filtro_str.encode()).hexdigest()
    
    return f"{hash_md5}.json"


def _is_cache_valid(cache_data):
    """
    Verifica se o cache ainda é válido baseado no timestamp.
    
    Args:
        cache_data: Dados do cache com campo 'timestamp'
    
    Returns:
        bool: True se o cache é válido
    """
    if 'timestamp' not in cache_data:
        return False
    
    try:
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        agora = datetime.now()
        diferenca = agora - cache_time
        
        return diferenca < timedelta(hours=CACHE_VALIDADE_HORAS)
    except:
        return False


def ler_cache_conferencia(data_inicial, data_final, preparador=''):
    """
    Lê cache de conferência se existir e for válido.
    
    Args:
        data_inicial: Data inicial (YYYY-MM-DD)
        data_final: Data final (YYYY-MM-DD)
        preparador: Nome do preparador (opcional)
    
    Returns:
        dict or None: Dados do cache ou None se não existir/inválido
    """
    try:
        filename = _get_cache_filename(data_inicial, data_final, preparador)
        filepath = os.path.join(CACHE_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"[DEBUG cache_conferencia] Cache não encontrado: {filename}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Verificar validade
        if not _is_cache_valid(cache_data):
            print(f"[DEBUG cache_conferencia] Cache expirado: {filename}")
            # Remover cache expirado
            os.remove(filepath)
            return None
        
        print(f"[DEBUG cache_conferencia] Cache válido encontrado: {filename}")
        return cache_data
        
    except Exception as e:
        print(f"[ERRO cache_conferencia] Erro ao ler cache: {e}")
        return None


def salvar_cache_conferencia(data_inicial, data_final, preparador, paletes):
    """
    Salva cache de conferência.
    
    Args:
        data_inicial: Data inicial (YYYY-MM-DD)
        data_final: Data final (YYYY-MM-DD)
        preparador: Nome do preparador
        paletes: Lista de paletes com status
    
    Returns:
        bool: True se salvou com sucesso
    """
    try:
        # Garantir que o diretório existe
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        filename = _get_cache_filename(data_inicial, data_final, preparador)
        filepath = os.path.join(CACHE_DIR, filename)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data_inicial': data_inicial,
            'data_final': data_final,
            'preparador': preparador,
            'total': len(paletes),
            'paletes': paletes
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        print(f"[DEBUG cache_conferencia] Cache salvo: {filename} ({len(paletes)} paletes)")
        return True
        
    except Exception as e:
        print(f"[ERRO cache_conferencia] Erro ao salvar cache: {e}")
        return False


def atualizar_palete_no_cache(data_inicial, data_final, preparador, viagem, palete, novo_status, novo_percentual):
    """
    Atualiza um palete específico no cache existente.
    
    Args:
        data_inicial: Data inicial (YYYY-MM-DD)
        data_final: Data final (YYYY-MM-DD)
        preparador: Nome do preparador
        viagem: Número da viagem
        palete: Número do palete
        novo_status: Novo status do palete
        novo_percentual: Novo percentual
    
    Returns:
        bool: True se atualizou com sucesso
    """
    try:
        cache_data = ler_cache_conferencia(data_inicial, data_final, preparador)
        
        if not cache_data:
            return False
        
        # Procurar e atualizar o palete
        paletes = cache_data.get('paletes', [])
        atualizado = False
        
        for p in paletes:
            if p['viagem'] == viagem and p['palete'] == palete:
                p['status'] = novo_status
                p['percentual'] = novo_percentual
                atualizado = True
                print(f"[DEBUG cache_conferencia] Palete {viagem}{palete} atualizado no cache")
                break
        
        if atualizado:
            # Salvar cache atualizado
            return salvar_cache_conferencia(data_inicial, data_final, preparador, paletes)
        
        return False
        
    except Exception as e:
        print(f"[ERRO cache_conferencia] Erro ao atualizar palete no cache: {e}")
        return False


def limpar_caches_antigos():
    """
    Remove todos os caches expirados.
    
    Returns:
        int: Quantidade de caches removidos
    """
    try:
        if not os.path.exists(CACHE_DIR):
            return 0
        
        removidos = 0
        
        for filename in os.listdir(CACHE_DIR):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(CACHE_DIR, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if not _is_cache_valid(cache_data):
                    os.remove(filepath)
                    removidos += 1
                    print(f"[DEBUG cache_conferencia] Cache expirado removido: {filename}")
            except:
                # Se houver erro ao ler, remover o arquivo
                os.remove(filepath)
                removidos += 1
        
        print(f"[DEBUG cache_conferencia] Limpeza concluída: {removidos} caches removidos")
        return removidos
        
    except Exception as e:
        print(f"[ERRO cache_conferencia] Erro ao limpar caches: {e}")
        return 0
