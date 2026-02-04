# 📋 Instruções para TI - Instalação do Denimax Dashboard

## Contexto
Este documento orienta a instalação do **Denimax Dashboard** como serviço do Windows, permitindo que o sistema rode automaticamente em background sem necessidade de manter terminal aberto.

---

## 🎯 Objetivo
Configurar o dashboard Flask para rodar como serviço do Windows, iniciando automaticamente com o sistema e rodando em background.

---

## 📦 Pré-requisitos

### Software necessário:
- ✅ Python 3.11.7 (já instalado)
- ✅ Driver ODBC iSeries Access (já instalado)
- ✅ Acesso à rede interna (para conexão com DB2)
- ⚠️ **Permissões de Administrador** (para instalar serviço)

### Arquivos do projeto:
Localização: `C:\Users\DCAPUCHINHO.ID-GROUP\Desktop\007\Site_dashboard_faturamento_Teste`

---

## 🔧 Procedimento de Instalação

### Passo 1: Preparar Ambiente Virtual

```powershell
# Navegar até a pasta do projeto
cd "C:\Users\DCAPUCHINHO.ID-GROUP\Desktop\007\Site_dashboard_faturamento_Teste"

# Criar ambiente virtual (se não existir)
python -m venv venv

# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### Passo 2: Instalar como Serviço Windows

**Opção A: Usar script automático (Recomendado)**

1. Botão direito em `instalar_servico.ps1`
2. Escolher **"Executar com PowerShell como Administrador"**
3. O script irá:
   - Baixar e instalar NSSM (Non-Sucking Service Manager)
   - Configurar o serviço "DenimaxDashboard"
   - Iniciar o serviço automaticamente

**Opção B: Instalação manual**

```powershell
# Executar como Administrador

# 1. Baixar NSSM
Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "$env:TEMP\nssm.zip"
Expand-Archive -Path "$env:TEMP\nssm.zip" -DestinationPath "$env:TEMP\nssm" -Force
New-Item -ItemType Directory -Path "C:\nssm" -Force
Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" -Destination "C:\nssm\nssm.exe"

# 2. Instalar serviço
$projectPath = "C:\Users\DCAPUCHINHO.ID-GROUP\Desktop\007\Site_dashboard_faturamento_Teste"
$pythonExe = "$projectPath\venv\Scripts\python.exe"

C:\nssm\nssm.exe install DenimaxDashboard $pythonExe "-m backend.app"
C:\nssm\nssm.exe set DenimaxDashboard AppDirectory $projectPath
C:\nssm\nssm.exe set DenimaxDashboard DisplayName "Denimax Production Dashboard"
C:\nssm\nssm.exe set DenimaxDashboard Description "Dashboard de producao - Sistema Denimax"
C:\nssm\nssm.exe set DenimaxDashboard Start SERVICE_AUTO_START

# 3. Configurar logs
New-Item -ItemType Directory -Path "$projectPath\logs" -Force
C:\nssm\nssm.exe set DenimaxDashboard AppStdout "$projectPath\logs\service.log"
C:\nssm\nssm.exe set DenimaxDashboard AppStderr "$projectPath\logs\service_error.log"

# 4. Iniciar serviço
C:\nssm\nssm.exe start DenimaxDashboard
```

### Passo 3: Verificar Instalação

```powershell
# Verificar status do serviço
Get-Service -Name DenimaxDashboard

# Deve mostrar: Status = Running
```

### Passo 4: Configurar Firewall (Acesso na rede)

```powershell
# Executar como Administrador
New-NetFirewallRule -DisplayName "Flask Denimax Dashboard" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

---

## 🌐 Acessos após Instalação

### Local (na própria máquina):
```
http://localhost:5000
```

### Rede interna:
```
http://[IP-DA-MAQUINA]:5000
```

Para descobrir o IP:
```powershell
ipconfig | findstr IPv4
```

---

## 🎮 Gerenciamento do Serviço

### Comandos úteis:

```powershell
# Parar serviço
C:\nssm\nssm.exe stop DenimaxDashboard

# Iniciar serviço
C:\nssm\nssm.exe start DenimaxDashboard

# Reiniciar serviço
C:\nssm\nssm.exe restart DenimaxDashboard

# Ver status
Get-Service -Name DenimaxDashboard

# Remover serviço
C:\nssm\nssm.exe stop DenimaxDashboard
C:\nssm\nssm.exe remove DenimaxDashboard confirm
```

### Via interface Windows:
1. Abrir **services.msc**
2. Localizar "Denimax Production Dashboard"
3. Clicar com botão direito para gerenciar

---

## 📊 Logs e Monitoramento

### Localização dos logs:
```
C:\Users\DCAPUCHINHO.ID-GROUP\Desktop\007\Site_dashboard_faturamento_Teste\logs\
```

Arquivos:
- `service.log` - Saída padrão da aplicação
- `service_error.log` - Erros e exceções

### Visualizar logs em tempo real:
```powershell
Get-Content ".\logs\service.log" -Wait -Tail 50
```

---

## 🔐 Considerações de Segurança

### Credenciais de banco:
- Armazenadas em: `backend/app/utils/settings_config.py`
- ⚠️ Arquivo **NÃO está no .gitignore**
- Recomendação: Mover credenciais para variáveis de ambiente

### Acesso à rede:
- Dashboard só funciona na rede interna da empresa
- Requer acesso ao sistema DB2 (FGE5006CDP)
- Porta 5000 deve estar liberada no firewall local

---

## ❌ Desinstalação

**Opção A: Usar script**
```powershell
# Executar como Administrador
.\remover_servico.ps1
```

**Opção B: Manual**
```powershell
C:\nssm\nssm.exe stop DenimaxDashboard
C:\nssm\nssm.exe remove DenimaxDashboard confirm
```

---

## 🆘 Troubleshooting

### Serviço não inicia:
1. Verificar se Python está no PATH
2. Verificar se ambiente virtual foi criado corretamente
3. Conferir logs em `logs/service_error.log`

### Erro de conexão com banco:
1. Verificar se driver ODBC iSeries está instalado
2. Confirmar conectividade com FGE5006CDP
3. Testar credenciais CDP174176G

### Porta 5000 já em uso:
1. Editar `backend/app/__main__.py`
2. Alterar linha: `app.run(debug=True, host='0.0.0.0', port=5000)`
3. Trocar porta (ex: 5001, 8080)
4. Reiniciar serviço

---

## 📞 Informações Adicionais

**Desenvolvedor:** Daniel Capuchinho (CDP174176G)
**Localização do Projeto:** Desktop do usuário DCAPUCHINHO
**Tecnologias:** Python 3.11.7 + Flask 3.0.0 + DB2 ODBC

**Dependências principais:**
- Flask 3.0.0
- Flask-CORS 4.0.0
- pyodbc 5.0.1 (requer driver ODBC iSeries)
- pandas 2.1.4
- gunicorn 23.0.0

---

## ✅ Checklist de Instalação

- [ ] Python 3.11.7 instalado
- [ ] Driver ODBC iSeries instalado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (requirements.txt)
- [ ] NSSM baixado e instalado em C:\nssm\
- [ ] Serviço "DenimaxDashboard" criado
- [ ] Serviço configurado para inicialização automática
- [ ] Logs configurados em logs/
- [ ] Firewall configurado (porta 5000)
- [ ] Serviço iniciado e rodando
- [ ] Dashboard acessível via http://localhost:5000
- [ ] Testes de funcionalidade OK

---

**Data de criação:** 01/01/2026
**Versão:** 1.0
