# 🚀 Como Rodar o Denimax na Empresa

## Pré-requisitos
- Python 3.11.7 instalado
- Driver ODBC iSeries instalado (já deve ter)
- Estar conectado à rede da empresa (ou VPN)

## Instalação (Primeira vez)

1. **Abrir PowerShell na pasta do projeto**

2. **Criar ambiente virtual:**
```powershell
python -m venv venv
```

3. **Ativar ambiente virtual:**
```powershell
.\venv\Scripts\Activate.ps1
```

4. **Instalar dependências:**
```powershell
pip install -r requirements.txt
```

## Como Iniciar o Servidor

### Opção 1: Usar o script automático (Mais fácil)
1. Clique duas vezes em **`iniciar_servidor.bat`**
2. Aguarde aparecer os endereços de acesso
3. Abra o navegador e acesse o link mostrado

### Opção 2: Manual via PowerShell
```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Iniciar servidor
python -m backend.app
```

## Acessar o Sistema

Após iniciar, você verá algo como:
```
Servidor iniciando...
Você pode acessar em:
  - Local: http://localhost:5000
  - Rede: http://192.168.1.100:5000
```

### No seu computador:
- Abra: `http://localhost:5000`

### Em outros computadores da rede:
- Abra: `http://192.168.1.100:5000` (use o IP mostrado no terminal)

## Parar o Servidor
- Pressione **Ctrl+C** no terminal
- Ou feche a janela

## Solução de Problemas

### Erro "python não encontrado"
- Verifique se Python está instalado: `python --version`
- Reinstale o Python se necessário

### Erro "ModuleNotFoundError"
- Execute novamente: `pip install -r requirements.txt`

### Erro de conexão com banco
- Verifique se está na rede da empresa ou VPN conectada
- Confirme que o driver ODBC iSeries está instalado

### Porta 5000 já em uso
- Edite `backend/app/__main__.py` e mude `port=5000` para outro número (ex: 5001, 8080)

## Configuração Firewall (Para acesso na rede)

Se outros computadores não conseguem acessar:

1. **Abrir PowerShell como Administrador**
2. **Executar:**
```powershell
New-NetFirewallRule -DisplayName "Flask Server" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

## Manutenção

### Atualizar código do GitHub
```powershell
git pull
```

### Atualizar dependências
```powershell
pip install -r requirements.txt --upgrade
```

## Contato
Para suporte, contate o administrador do sistema.
