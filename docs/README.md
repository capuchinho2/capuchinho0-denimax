# Dashboard de Faturamento - Sistema HET e HOM

Sistema web para visualização em tempo real dos volumes de produção HET (Heterogêneo) e HOM (Homogêneo).

## 📋 Pré-requisitos

### Windows
- Python 3.8 ou superior
- Driver ODBC iSeries Access instalado
- Navegador web moderno (Chrome, Firefox, Edge)

## 🚀 Instalação

### 1. Criar ambiente virtual Python

```powershell
# Na pasta do projeto
python -m venv venv
```

### 2. Ativar o ambiente virtual

```powershell
.\venv\Scripts\Activate
```

### 3. Instalar dependências

```powershell
pip install -r requirements.txt
```

### 4. Configurar credenciais do banco de dados

Edite o arquivo `config.py` com suas credenciais:

```python
DB_CONFIG = {
    "DRIVER": "{iSeries Access ODBC Driver}",
    "SYSTEM": "SEU_SISTEMA",
    "UID": "SEU_USUARIO",
    "PWD": "SUA_SENHA"
}
```

⚠️ **IMPORTANTE**: Nunca compartilhe o arquivo `config.py` em repositórios públicos!

## 🎯 Como Usar

### 1. Iniciar o servidor (Backend + Frontend)

```powershell
python app.py
```

O servidor iniciará em `http://localhost:5000`

Você verá a mensagem:
```
 * Running on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
 * Debugger is active!
```

### 2. Abrir o dashboard

**Abra seu navegador e acesse:**
```
http://localhost:5000
```

⚠️ **IMPORTANTE**: Use `http://localhost:5000` no navegador, não abra o arquivo `index.html` diretamente!

## 📊 Funcionalidades

### Dashboard Principal
- ✅ Visualização de volumes HET (preparado e pendente)
- ✅ Visualização de volumes HOM (preparado e pendente)
- ✅ Total consolidado HET + HOM
- ✅ Gráficos interativos em tempo real
- ✅ Atualização automática a cada 5 minutos
- ✅ Filtro por data

### API Endpoints

#### 1. Verificar saúde da API
```
GET /api/health
```

Resposta:
```json
{
  "status": "ok",
  "message": "API está funcionando"
}
```

#### 2. Buscar volumes do dia atual
```
GET /api/volumes/hoje
```

Resposta:
```json
{
  "success": true,
  "data": {
    "data": "20251116",
    "het": {
      "preparado": 123.45,
      "pendente": 67.89,
      "total": 191.34,
      "preparado_kg": 123450.00,
      "pendente_kg": 67890.00
    },
    "hom": {
      "preparado": 234.56,
      "pendente": 78.90,
      "total": 313.46,
      "preparado_kg": 234560.00,
      "pendente_kg": 78900.00
    },
    "consolidado": {
      "preparado": 358.01,
      "pendente": 146.79,
      "total": 504.80
    }
  }
}
```

#### 3. Buscar volumes por período
```
POST /api/volumes
Content-Type: application/json

{
  "data_inicial": "20251101",
  "data_final": "20251115"
}
```

Resposta: Mesmo formato do endpoint `/api/volumes/hoje`

## 🔧 Estrutura do Projeto

```
Site_dashboard_faturamento/
├── app.py                          # Servidor Flask (API Backend)
├── config.py                       # Configurações do banco de dados
├── requirements.txt                # Dependências Python
├── .gitignore                      # Arquivos ignorados pelo Git
├── index.html                      # Dashboard principal
├── script.js                       # Lógica do frontend
├── styles.css                      # Estilos do dashboard
├── Volume_HET_e_HOM_Consolidado.py # Script original (referência)
└── README.md                       # Este arquivo
```

## 🛠️ Desenvolvimento

### Script Original vs API

O arquivo `Volume_HET_e_HOM_Consolidado.py` é o script original que:
- Roda via linha de comando
- Solicita datas interativamente
- Exporta resultados para Excel

A nova API (`app.py`):
- Converte a lógica do script em endpoints REST
- Permite integração com frontend web
- Retorna dados em formato JSON
- Suporta consultas automáticas

### Tecnologias Utilizadas

**Backend:**
- Flask - Framework web Python
- Flask-CORS - Suporte a requisições cross-origin
- pyodbc - Conexão com banco de dados DB2/iSeries
- pandas - Manipulação de dados

**Frontend:**
- HTML5, CSS3, JavaScript (ES6+)
- Chart.js - Gráficos interativos
- Font Awesome - Ícones
- Google Fonts - Tipografia

## 🐛 Solução de Problemas

### Erro: "Não foi possível carregar os dados"

1. Verifique se o servidor Flask está rodando
2. Verifique a URL da API em `script.js` (deve ser `http://localhost:5000/api`)
3. Veja os logs do console do navegador (F12)

### Erro: "pyodbc.Error: ('08001'..."

1. Verifique se o driver ODBC iSeries Access está instalado
2. Confirme que as credenciais em `config.py` estão corretas
3. Teste a conexão com o banco de dados

### Frontend não carrega dados

1. Abra o Console do navegador (F12)
2. Verifique se há erros de CORS
3. Confirme que `Flask-CORS` está instalado no backend

### Gráficos não aparecem

1. Verifique se Chart.js está carregando (veja Network tab no F12)
2. Confirme que os elementos `<canvas>` existem no HTML
3. Veja se há erros no console JavaScript

## 📝 Notas Importantes

- Os dados são consultados diretamente do banco de dados de produção
- O sistema calcula automaticamente os totais consolidados
- HET usa dados da tabela ONDAITM (RCAIXAS vs QTDLIDA)
- HOM usa dados da tabela GESUPE (campo CARDES)
- Ambos processam apenas viagens tipo 'STD'

## 🔐 Segurança

- Nunca comite o arquivo `config.py` em repositórios públicos
- Use variáveis de ambiente em produção
- Considere implementar autenticação para a API
- Configure HTTPS em ambiente de produção

## 📧 Suporte

Para dúvidas ou problemas, consulte a documentação interna ou entre em contato com a equipe de TI.

---

**Versão:** 1.0.0  
**Data:** 16/11/2025
