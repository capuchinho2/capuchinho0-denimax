# Produtividade Preparadores - Python

Sistema de análise de produtividade dos preparadores convertido de PHP para Python.

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Edite o arquivo `config.py` com as credenciais dos seus bancos de dados:

- **DB2**: Sistema principal (RASTLOG, ONDAITM, GEZPRP, GEPRO)
- **MySQL**: Tabela de erros (tabela_erros, tabela_ring)

## Uso

### 1. Produtividade por Período

```bash
python produtividade_dia.py
```

### 2. Produtividade Hoje

```bash
python produtividade_hoje.py
```

### 3. Produtividade por Colaborador

```bash
python produtividade_colaborador.py
```

## Estrutura

```
python/
├── config.py                     # Configurações de banco
├── db_connection.py              # Classes de conexão DB2/MySQL
├── utils.py                      # Funções auxiliares (joins, cálculos)
├── produtividade_dia.py          # Produtividade por período
├── produtividade_hoje.py         # Produtividade do dia
├── produtividade_colaborador.py  # Produtividade individual
└── requirements.txt              # Dependências
```

## Saída

Os scripts imprimem logs detalhados no terminal mostrando:
- ✓ Conexões estabelecidas
- ✓ Queries executadas
- ✓ Joins e cálculos realizados
- 📊 Tabelas formatadas com os resultados
