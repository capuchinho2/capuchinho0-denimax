from typing import List, Dict, Any

def left_join_arrays(arr1: List[Dict], arr2: List[Dict], key1: str, key2: str) -> List[Dict]:
    """Simula LEFT JOIN entre dois arrays"""
    result = []
    
    # Cria dicionário do arr2 para lookup rápido
    arr2_dict = {item[key2]: item for item in arr2 if key2 in item}
    
    for item1 in arr1:
        merged = item1.copy()
        key_value = item1.get(key1)
        
        if key_value and key_value in arr2_dict:
            # Merge dos dados do arr2
            for k, v in arr2_dict[key_value].items():
                if k != key2:  # Não duplicar a chave
                    merged[k] = v
        
        result.append(merged)
    
    return result


def calc_subtraction(arr: List[Dict], field1: str, field2: str, result_field: str, round_digits: int = 3) -> List[Dict]:
    """Calcula subtração entre dois campos"""
    result = []
    
    for item in arr:
        new_item = item.copy()
        val1 = float(item.get(field1, 0) or 0)
        val2 = float(item.get(field2, 0) or 0)
        new_item[result_field] = round(val1 - val2, round_digits)
        result.append(new_item)
    
    return result


def calc_percentage(arr: List[Dict], field: str, result_field: str) -> List[Dict]:
    """Calcula percentual de um campo em relação ao total"""
    # Calcula o total
    total = sum(float(item.get(field, 0) or 0) for item in arr)
    
    result = []
    for item in arr:
        new_item = item.copy()
        val = float(item.get(field, 0) or 0)
        new_item[result_field] = round((val / total * 100) if total > 0 else 0, 2)
        result.append(new_item)
    
    return result


def print_table(data: List[Dict], title: str = ""):
    """Imprime dados em formato de tabela no console"""
    if not data:
        print("\n⚠ Nenhum dado encontrado")
        return
    
    print(f"\n{'='*80}")
    if title:
        print(f"{title}")
        print(f"{'='*80}")
    
    # Pega as colunas
    headers = list(data[0].keys())
    
    # Calcula largura de cada coluna
    col_widths = {}
    for header in headers:
        col_widths[header] = max(
            len(str(header)),
            max(len(str(row.get(header, ''))) for row in data)
        )
    
    # Imprime cabeçalho
    header_row = " | ".join(str(h).ljust(col_widths[h]) for h in headers)
    print(header_row)
    print("-" * len(header_row))
    
    # Imprime dados
    for row in data:
        print(" | ".join(str(row.get(h, '')).ljust(col_widths[h]) for h in headers))
    
    print(f"{'='*80}")
    print(f"Total de registros: {len(data)}\n")
