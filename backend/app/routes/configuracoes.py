from flask import Blueprint, render_template, render_template_string, jsonify
import os
from pathlib import Path

configuracoes_bp = Blueprint('configuracoes', __name__)
checklist_bp = Blueprint('checklist', __name__)

@configuracoes_bp.route('/configuracoes')
def configuracoes_page():
    return render_template('configuracoes.html')


@checklist_bp.route('/checklist')
def checklist_page():
        return render_template_string('''
        <!doctype html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Checklist | Denimax</title>
            <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        </head>
        <body>
            <div class="dashboard-container">
                <aside class="sidebar">
                    <div class="sidebar-header">
                        <div class="logo"><div class="logo-icon"><i class="fas fa-industry"></i></div><div class="logo-text">Denimax</div></div>
                        <div class="logo-subtitle" style="color: var(--text-muted); font-size: 0.8rem;">Sistema de Produção v2.1</div>
                    </div>
                    <nav><ul class="nav-menu">
                        <li class="nav-item"><a href="/checklist" class="nav-link active"><i class="fas fa-list-check"></i>Checklist</a></li>
                    </ul></nav>
                </aside>
                <main class="main-content">
                    <header class="header">
                        <div class="header-info">
                            <h1 class="header-title"><i class="fas fa-clipboard-check"></i> Checklist</h1>
                            <p class="header-subtitle">Coleta e acompanhamento dos checklists operacionais</p>
                        </div>
                        <div class="datetime-display">
                            <div class="current-time" id="currentTime">--:--:--</div>
                            <div class="current-date" id="currentDate">--/--/----</div>
                        </div>
                    </header>
                    <section class="metrics-grid checklist-metrics-grid" style="margin-bottom: 1.5rem;">
                        <div class="metric-card">
                            <div class="metric-header"><div class="metric-icon" style="background:linear-gradient(135deg,#00d4ff15,#0066cc15);color:var(--primary-color);"><i class="fas fa-clipboard-list"></i></div></div>
                            <div class="metric-content"><div class="metric-value" id="totalChecklists">0</div><div class="metric-label">Checklists encontrados</div></div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-header"><div class="metric-icon" style="background:linear-gradient(135deg,#ffaa0015,#ff6b3515);color:var(--warning-color);"><i class="fas fa-clock"></i></div></div>
                            <div class="metric-content"><div class="metric-value" id="turnoAtual">-</div><div class="metric-label">Turno atual</div></div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-header"><div class="metric-icon" style="background:rgba(0,255,136,0.1);color:var(--success-color);"><i class="fas fa-check-circle"></i></div></div>
                            <div class="metric-content"><div class="metric-value" id="totalAprovados">0</div><div class="metric-label">Aprovados</div></div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-header"><div class="metric-icon" style="background:rgba(255,71,87,0.1);color:var(--danger-color);"><i class="fas fa-times-circle"></i></div></div>
                            <div class="metric-content"><div class="metric-value" id="totalCriados">0</div><div class="metric-label">Criados</div></div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-header"><div class="metric-icon" style="background:rgba(255,170,0,0.1);color:var(--warning-color);"><i class="fas fa-spinner"></i></div></div>
                            <div class="metric-content"><div class="metric-value" id="totalEmAndamento">0</div><div class="metric-label">Em andamento</div></div>
                        </div>
                    </section>
                    <div class="metric-card" style="padding: 1.5rem;">
                        <div style="display:flex; gap:1rem; flex-wrap:wrap; align-items:end; margin-bottom:1.5rem;">
                            <label style="color:var(--text-primary);">Data inicial<br><input id="checklistDataInicial" class="checklist-filter-control" type="date"></label>
                            <label style="color:var(--text-primary);">Data final<br><input id="checklistDataFinal" class="checklist-filter-control" type="date"></label>
                            <label style="color:var(--text-primary);">Status<br>
                                <div id="checklistStatusWrapper" class="checklist-multi-select">
                                    <button id="checklistStatusBotao" class="checklist-status-select" type="button">Todos <i class="fas fa-chevron-down"></i></button>
                                    <div id="checklistStatusOpcoes" class="checklist-multi-options">
                                        <label class="checklist-multi-option"><input type="checkbox" value="Aprovado"> <span>Aprovado</span></label>
                                        <label class="checklist-multi-option"><input type="checkbox" value="Criado"> <span>Criado</span></label>
                                        <label class="checklist-multi-option"><input type="checkbox" value="Em Andamento"> <span>Em Andamento</span></label>
                                    </div>
                                </div>
                            </label>
                            <label style="color:var(--text-primary);">Nome<br>
                                <div id="checklistResponsavelWrapper" class="checklist-multi-select">
                                    <button id="checklistResponsavelBotao" class="checklist-filter-select" type="button">Todos os nomes <i class="fas fa-chevron-down"></i></button>
                                    <div id="checklistResponsavelOpcoes" class="checklist-multi-options"></div>
                                </div>
                            </label>
                            <div style="display:flex; gap:0.5rem; align-items:end;">
                                <button class="btn btn-turno" data-turno="TURNO 1" type="button"><i class="fas fa-sun"></i> Turno 1</button>
                                <button class="btn btn-turno" data-turno="TURNO 2" type="button"><i class="fas fa-cloud-sun"></i> Turno 2</button>
                                <button class="btn btn-turno" data-turno="TURNO 3" type="button"><i class="fas fa-moon"></i> Turno 3</button>
                                <button id="btnLimparFiltrosChecklists" class="btn btn-limpar-filtros" type="button" title="Limpar filtros" aria-label="Limpar filtros"><i class="fas fa-eraser"></i></button>
                            </div>
                            <button id="btnCarregarChecklists" class="btn btn-primary" type="button"><i class="fas fa-sync-alt"></i> Carregar checklists</button>
                            <button id="btnModoAutomacao" class="btn btn-modo-automacao" type="button"><i id="iconeModoAutomacao" class="fas fa-hand-pointer"></i> <span id="textoModoAutomacao">Manual</span></button>
                            <button id="btnResumoNomes" class="btn btn-resumo-nomes" type="button"><i id="iconeResumoNomes" class="fas fa-users"></i> <span id="textoResumoNomes">Mostrar</span></button>
                            <button id="btnEnviarChecklists" class="btn btn-success" type="button" disabled><i class="fas fa-paper-plane"></i> Enviar pelo Telegram</button>
                        </div>
                        <p id="checklistMensagem" style="color:var(--text-secondary);">Nenhum checklist carregado.</p>
                        <div id="containerResumoNomes" style="display:none; margin-bottom:1.5rem;">
                            <div style="overflow-x:auto; background:rgba(45, 52, 71, 0.8); border-radius:10px; border:1px solid rgba(255,255,255,0.08); padding:1rem;">
                                <table class="table-bordered table-striped data-table checklist-table" style="width:100%; color:var(--text-primary);">
                                    <thead><tr><th>Nome</th><th>N° checklist</th></tr></thead>
                                    <tbody id="corpoResumoNomes"><tr><td colspan="2" style="padding:20px;">Clique em Carregar checklists para gerar o resumo.</td></tr></tbody>
                                </table>
                            </div>
                        </div>
                        <div id="checklistTabela" style="overflow:auto;"></div>
                    </div>
                            <script>
                                const dataHoje = new Date().toISOString().slice(0, 10);
                                const dataInicial = document.getElementById('checklistDataInicial');
                                const dataFinal = document.getElementById('checklistDataFinal');
                                const statusWrapper = document.getElementById('checklistStatusWrapper');
                                const statusBotao = document.getElementById('checklistStatusBotao');
                                const statusOpcoes = document.getElementById('checklistStatusOpcoes');
                                const responsavelWrapper = document.getElementById('checklistResponsavelWrapper');
                                const responsavelBotao = document.getElementById('checklistResponsavelBotao');
                                const responsavelOpcoes = document.getElementById('checklistResponsavelOpcoes');
                                const mensagem = document.getElementById('checklistMensagem');
                                const tabela = document.getElementById('checklistTabela');
                                const btnCarregar = document.getElementById('btnCarregarChecklists');
                                const btnLimparFiltros = document.getElementById('btnLimparFiltrosChecklists');
                                const btnModoAutomacao = document.getElementById('btnModoAutomacao');
                                const textoModoAutomacao = document.getElementById('textoModoAutomacao');
                                const iconeModoAutomacao = document.getElementById('iconeModoAutomacao');
                                const btnResumoNomes = document.getElementById('btnResumoNomes');
                                const btnEnviar = document.getElementById('btnEnviarChecklists');
                                const totalChecklists = document.getElementById('totalChecklists');
                                const turnoAtual = document.getElementById('turnoAtual');
                                const totalAprovados = document.getElementById('totalAprovados');
                                const totalCriados = document.getElementById('totalCriados');
                                const totalEmAndamento = document.getElementById('totalEmAndamento');
                                const botoesTurno = document.querySelectorAll('.btn-turno[data-turno]');
                                const containerResumoNomes = document.getElementById('containerResumoNomes');
                                const corpoResumoNomes = document.getElementById('corpoResumoNomes');
                                let checklistsCarregados = [];
                                let turnoSelecionado = 'Todos';
                                let resumoNomesVisivel = false;
                                let modoAutomatico = false;
                                let intervaloAutomatico = null;

                                function nomesSelecionados() {
                                    return [...responsavelOpcoes.querySelectorAll('input:checked')].map(input => input.value);
                                }

                                function statusSelecionados() {
                                    return [...statusOpcoes.querySelectorAll('input:checked')].map(input => input.value);
                                }

                                function atualizarTextoStatus() {
                                    const selecionados = statusSelecionados();
                                    statusBotao.innerHTML = selecionados.length ?
                                        selecionados.length + ' status selecionado(s) <i class="fas fa-chevron-down"></i>' :
                                        'Todos <i class="fas fa-chevron-down"></i>';
                                }

                                function atualizarTextoNomes() {
                                    const nomes = nomesSelecionados();
                                    responsavelBotao.innerHTML = nomes.length ?
                                        nomes.length + ' nome(s) selecionado(s) <i class="fas fa-chevron-down"></i>' :
                                        'Todos os nomes <i class="fas fa-chevron-down"></i>';
                                }

                                function limparFiltrosManuais() {
                                    statusOpcoes.querySelectorAll('input').forEach(input => input.checked = false);
                                    responsavelOpcoes.querySelectorAll('input').forEach(input => input.checked = false);
                                    atualizarTextoStatus();
                                    atualizarTextoNomes();
                                    turnoSelecionado = 'Todos';
                                    botoesTurno.forEach(item => item.classList.remove('active'));
                                }

                                btnLimparFiltros.addEventListener('click', function() {
                                    limparFiltrosManuais();
                                    mensagem.textContent = checklistsCarregados.length + ' checklist(s) encontrado(s).';
                                    desenharTabela();
                                });

                                responsavelBotao.addEventListener('click', function() {
                                    responsavelWrapper.classList.toggle('open');
                                });

                                statusBotao.addEventListener('click', function() {
                                    statusWrapper.classList.toggle('open');
                                });

                                document.addEventListener('click', function(evento) {
                                    if (!responsavelWrapper.contains(evento.target)) responsavelWrapper.classList.remove('open');
                                    if (!statusWrapper.contains(evento.target)) statusWrapper.classList.remove('open');
                                });

                                statusOpcoes.querySelectorAll('input').forEach(input => input.addEventListener('change', function() {
                                    atualizarTextoStatus();
                                    mensagem.textContent = 'Filtro por status atualizado.';
                                    desenharTabela();
                                }));
                                atualizarTextoStatus();

                                dataInicial.value = dataHoje;
                                dataFinal.value = dataHoje;

                                function formatoApi(data) {
                                    const partes = data.split('-');
                                    return partes.reverse().join('/');
                                }

                                function toggleDropdown(button) {
                                    button.classList.toggle('active');
                                    button.nextElementSibling.classList.toggle('show');
                                }

                                function atualizarRelogio() {
                                    const agora = new Date();
                                    document.getElementById('currentTime').textContent = agora.toLocaleTimeString('pt-BR');
                                    document.getElementById('currentDate').textContent = agora.toLocaleDateString('pt-BR');
                                    const hora = agora.getHours() * 60 + agora.getMinutes();
                                    turnoAtual.textContent = hora >= 370 && hora <= 879 ? 'TURNO 1' : hora >= 880 && hora <= 1390 ? 'TURNO 2' : 'TURNO 3';
                                }
                                atualizarRelogio();
                                setInterval(atualizarRelogio, 1000);

                                function desenharResumoNomes() {
                                    const grupos = new Map();
                                    checklistsCarregados.forEach(item => {
                                        const statusItem = (item.status || '').trim().toLowerCase();
                                        if (statusItem !== 'criado' && statusItem !== 'em andamento') return;
                                        const nome = (item.responsavel || 'Não informado').trim();
                                        if (!grupos.has(nome)) grupos.set(nome, {nome, total: 0});
                                        grupos.get(nome).total += 1;
                                    });
                                    const resumo = [...grupos.values()].sort((a, b) => b.total - a.total || a.nome.localeCompare(b.nome, 'pt-BR'));
                                    corpoResumoNomes.innerHTML = resumo.length ? resumo.map(item =>
                                        '<tr><td>' + item.nome + '</td><td>' + item.total + '</td></tr>'
                                    ).join('') : '<tr><td colspan="2" style="padding:20px; color:var(--text-secondary);">Nenhum checklist Criado ou Em Andamento encontrado.</td></tr>';
                                }

                                btnResumoNomes.addEventListener('click', function() {
                                    resumoNomesVisivel = !resumoNomesVisivel;
                                    containerResumoNomes.style.display = resumoNomesVisivel ? 'block' : 'none';
                                    document.getElementById('textoResumoNomes').textContent = resumoNomesVisivel ? 'Ocultar' : 'Mostrar';
                                    document.getElementById('iconeResumoNomes').className = resumoNomesVisivel ? 'fas fa-eye-slash' : 'fas fa-eye';
                                    if (resumoNomesVisivel) desenharResumoNomes();
                                });

                                function obterChecklistsVisiveis() {
                                    const nomes = nomesSelecionados();
                                    const statusFiltro = statusSelecionados();
                                    return checklistsCarregados.filter(item => {
                                        const turnoValido = turnoSelecionado === 'Todos' || item.turno === turnoSelecionado;
                                        const nomeValido = !nomes.length || nomes.includes(item.responsavel);
                                        const statusValido = !statusFiltro.length || statusFiltro.includes(item.status);
                                        return turnoValido && nomeValido && statusValido;
                                    });
                                }

                                function desenharTabela() {
                                    const nomesDestacados = new Set([
                                        'EDUARDO CORREA VICENTE',
                                        'DJAIR GUIMARAES BISPO DE ALMEIDA',
                                        'ED CARLOS DA SILVA',
                                        'ANDERSON HONORIO DA SILVA',
                                        'FILIPE AUGUSTO MOREIRA'
                                    ]);
                                    const checklistsVisiveis = obterChecklistsVisiveis();
                                    totalChecklists.textContent = checklistsVisiveis.length;
                                    btnEnviar.disabled = !checklistsVisiveis.length;
                                    const contagemStatus = checklistsVisiveis.reduce((contagem, item) => {
                                        const statusItem = (item.status || '').trim().toLowerCase();
                                        if (statusItem === 'aprovado') contagem.aprovado += 1;
                                        if (statusItem === 'criado') contagem.criado += 1;
                                        if (statusItem === 'em andamento') contagem.emAndamento += 1;
                                        return contagem;
                                    }, {aprovado: 0, criado: 0, emAndamento: 0});
                                    totalAprovados.textContent = contagemStatus.aprovado;
                                    totalCriados.textContent = contagemStatus.criado;
                                    totalEmAndamento.textContent = contagemStatus.emAndamento;
                                    const linhas = checklistsVisiveis.map(item => {
                                        const statusNormalizado = (item.status || '').trim().toLowerCase();
                                        const nomeNormalizado = (item.responsavel || '').trim().toUpperCase();
                                        let corLinha = '';
                                        if (nomesDestacados.has(nomeNormalizado)) {
                                            corLinha = 'background-color: rgba(155, 89, 182, 0.35);';
                                        } else {
                                            if (statusNormalizado === 'aprovado') {
                                                corLinha = 'background-color: rgba(0, 255, 136, 0.18);';
                                            } else if (statusNormalizado === 'criado') {
                                                corLinha = 'background-color: rgba(255, 71, 87, 0.18);';
                                            } else if (statusNormalizado === 'em andamento') {
                                                corLinha = 'background-color: rgba(255, 170, 0, 0.2);';
                                            }
                                        }
                                        return '<tr style="' + corLinha + '"><td>' + item.codigo + '</td><td>' + item.responsavel + '</td><td>' + item.checklist + '</td><td>' + item.informacoes + '</td><td>' + item.percentual + '</td><td>' + item.status + '</td><td>' + item.data_hora + '</td><td>' + item.turno + '</td></tr>';
                                    }).join('');
                                    tabela.innerHTML = checklistsVisiveis.length ?
                                        '<table class="table-bordered table-striped data-table checklist-table" style="width:100%; color:var(--text-primary); min-width:1000px"><thead><tr><th>Código</th><th>Nome</th><th>Checklist</th><th>N° Equip</th><th>Percentual</th><th>Status</th><th>Data</th><th>Turno</th></tr></thead><tbody>' +
                                        linhas +
                                        '</tbody></table>' : '';
                                }

                                function atualizarNomes() {
                                    const nomes = [...new Set(
                                        checklistsCarregados
                                            .map(item => (item.responsavel || '').trim())
                                            .filter(Boolean)
                                    )].sort((a, b) => a.localeCompare(b, 'pt-BR'));
                                    responsavelOpcoes.innerHTML = nomes.map(nome =>
                                        '<label class="checklist-multi-option"><input type="checkbox" value="' + nome.replace(/"/g, '&quot;') + '"> <span>' + nome + '</span></label>'
                                    ).join('');
                                    responsavelOpcoes.querySelectorAll('input').forEach(input => input.addEventListener('change', function() {
                                        atualizarTextoNomes();
                                        mensagem.textContent = 'Filtro por nome atualizado.';
                                        desenharTabela();
                                    }));
                                    atualizarTextoNomes();
                                }

                                botoesTurno.forEach(botao => {
                                    botao.addEventListener('click', function() {
                                        const turno = this.dataset.turno;
                                        turnoSelecionado = turnoSelecionado === turno ? 'Todos' : turno;
                                        botoesTurno.forEach(item => item.classList.toggle('active', item === this && turnoSelecionado !== 'Todos'));
                                        btnEnviar.disabled = !obterChecklistsVisiveis().length;
                                        mensagem.textContent = turnoSelecionado === 'Todos' ?
                                            checklistsCarregados.length + ' checklist(s) encontrado(s).' :
                                            'Filtro ' + turnoSelecionado + ': ' + checklistsCarregados.filter(item => item.turno === turnoSelecionado).length + ' checklist(s).';
                                        desenharTabela();
                                    });
                                });

                                async function carregarChecklistsAutomaticamente() {
                                    try {
                                        const resposta = await fetch('/api/checklist/coletar-auto');
                                        const resultado = await resposta.json();
                                        if (!resultado.success) throw new Error(resultado.error);
                                        checklistsCarregados = resultado.dados;
                                        limparFiltrosManuais();
                                        atualizarNomes();
                                        desenharResumoNomes();
                                        mensagem.textContent = resultado.total + ' checklist(s) pendente(s) encontrados entre ' +
                                            resultado.periodo.data_inicial + ' e ' + resultado.periodo.data_final + '.';
                                        desenharTabela();
                                    } catch (erro) {
                                        mensagem.textContent = 'Erro na busca automática: ' + erro.message;
                                    }
                                }

                                btnModoAutomacao.addEventListener('click', function() {
                                    modoAutomatico = !modoAutomatico;
                                    textoModoAutomacao.textContent = modoAutomatico ? 'Auto' : 'Manual';
                                    iconeModoAutomacao.className = modoAutomatico ? 'fas fa-robot' : 'fas fa-hand-pointer';
                                    btnModoAutomacao.classList.toggle('active', modoAutomatico);
                                    btnCarregar.disabled = modoAutomatico;

                                    if (modoAutomatico) {
                                        carregarChecklistsAutomaticamente();
                                        intervaloAutomatico = setInterval(carregarChecklistsAutomaticamente, 60000);
                                        mensagem.textContent = 'Modo automático ativado. Atualização a cada 1 minuto.';
                                    } else {
                                        clearInterval(intervaloAutomatico);
                                        intervaloAutomatico = null;
                                        mensagem.textContent = 'Modo manual ativado.';
                                    }
                                });

                                btnCarregar.onclick = async function() {
                                    if (modoAutomatico) return;
                                    mensagem.textContent = 'Coletando checklists...';
                                    btnEnviar.disabled = true;
                                    try {
                                        const parametros = new URLSearchParams({
                                            data_inicial: formatoApi(dataInicial.value),
                                            data_final: formatoApi(dataFinal.value),
                                            status: statusSelecionados().length === 1 ? statusSelecionados()[0] : 'Todos'
                                        });
                                        const resposta = await fetch('/api/checklist/coletar?' + parametros);
                                        const resultado = await resposta.json();
                                        if (!resultado.success) throw new Error(resultado.error);
                                        checklistsCarregados = resultado.dados;
                                        desenharResumoNomes();
                                        atualizarNomes();
                                        turnoSelecionado = 'Todos';
                                        botoesTurno.forEach(item => item.classList.remove('active'));
                                        totalChecklists.textContent = resultado.total;
                                        mensagem.textContent = resultado.total + ' checklist(s) encontrado(s).';
                                        btnEnviar.disabled = !checklistsCarregados.length;
                                        desenharTabela();
                                    } catch (erro) {
                                        mensagem.textContent = 'Erro: ' + erro.message;
                                        tabela.innerHTML = '';
                                    }
                                };

                                btnEnviar.onclick = async function() {
                                    mensagem.textContent = 'Enviando mensagem pelo Telegram...';
                                    try {
                                        const resposta = await fetch('/api/checklist/enviar-telegram', {
                                            method: 'POST',
                                            headers: {'Content-Type': 'application/json'},
                                            body: JSON.stringify({checklists: obterChecklistsVisiveis()})
                                        });
                                        const resultado = await resposta.json();
                                        if (!resultado.success) throw new Error(resultado.error);
                                        mensagem.textContent = 'Mensagem enviada para ' + resultado.responsavel + '.';
                                    } catch (erro) {
                                        mensagem.textContent = 'Erro ao enviar: ' + erro.message;
                                    }
                                };
                            </script>
                </main>
            </div>
        </body>
        </html>
        ''')

@configuracoes_bp.route('/configuracoes/limpar-cache-paletes', methods=['POST'])
def limpar_cache_paletes():
    base_dir = Path(__file__).parent.parent.parent
    dir_path = base_dir / 'cache_paletes'
    total_apagados = 0
    if dir_path.exists() and dir_path.is_dir():
        for f in dir_path.iterdir():
            if f.is_file():
                f.unlink()
                total_apagados += 1
    return jsonify({'success': True, 'apagados': total_apagados, 'message': f'{total_apagados} arquivos apagados em cache_paletes.'})

@configuracoes_bp.route('/configuracoes/limpar-cash-plts', methods=['POST'])
def limpar_cash_plts():
    base_dir = Path(__file__).parent.parent.parent
    dir_path = base_dir / 'cash_plts'
    total_apagados = 0
    if dir_path.exists() and dir_path.is_dir():
        for f in dir_path.iterdir():
            if f.is_file():
                f.unlink()
                total_apagados += 1
    return jsonify({'success': True, 'apagados': total_apagados, 'message': f'{total_apagados} arquivos apagados em cash_plts.'})
