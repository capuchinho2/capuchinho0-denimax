// Função real para buscar e exibir paletes preparados
async function carregarPaletesPreparados() {
    const dataInicial = document.getElementById('dataInicialPrep')?.value;
    const dataFinal = document.getElementById('dataFinalPrep')?.value;
    const nomePreparador = document.getElementById('nomePreparador')?.value || '';
    if (!dataInicial || !dataFinal) {
        alert('Por favor, selecione o período!');
        return;
    }
    try {
                const url = `/status-prep/preparados?dataInicial=${dataInicial}&dataFinal=${dataFinal}&preparador=${encodeURIComponent(nomePreparador)}`;
                const resp = await fetch(url);
                const resultado = await resp.json();
                // O backend retorna { success, total, dados: [] }
                const totalSpan = document.getElementById('paletesPreparados');
                if (totalSpan) totalSpan.textContent = resultado.total || 0;
                const tbody = document.getElementById('corpoTabelaPreparados');
                if (tbody) {
                    const lista = Array.isArray(resultado.dados) ? resultado.dados : [];
                    if (lista.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="3" style="padding: 20px; text-align: center; color: var(--text-secondary);">Nenhum palete preparado encontrado</td></tr>`;
                    } else {
                        tbody.innerHTML = lista.map(item => `
                            <tr style="border-bottom:1px solid var(--border-color);">
                                <td style="padding:12px; color:var(--text-primary);">${item.viagem || ''}</td>
                                <td style="padding:12px; color:var(--text-primary);">${item.palete}</td>
                                <td style="padding:12px; color:var(--text-primary);">${item.prep || ''}</td>
                            </tr>
                        `).join('');
                    }
                }
    } catch (e) {
        alert('Erro ao buscar paletes preparados: ' + e.message);
    }
}
window.carregarPaletesPreparados = carregarPaletesPreparados;
// Função real para buscar e exibir viagens pendentes
async function carregarStatusPrep() {
    const dataInicial = document.getElementById('dataInicialPrep')?.value;
    const dataFinal = document.getElementById('dataFinalPrep')?.value;
    const nomePreparador = document.getElementById('nomePreparador')?.value || '';
    if (!dataInicial || !dataFinal) {
        alert('Por favor, selecione o período!');
        return;
    }
        try {
                const url = `/api/status-prep?dataInicial=${dataInicial}&dataFinal=${dataFinal}&preparador=${encodeURIComponent(nomePreparador)}`;
                const resp = await fetch(url);
                const resultado = await resp.json();
                console.log('Resultado status-prep:', resultado);
                // Exemplo: preencher o total de preparados e incompletos
                document.getElementById('totalPreparados').textContent = resultado.preparados || 0;
                document.getElementById('totalIncompletos').textContent = resultado.incompletos || 0;
                // Exemplo: preencher tabela de pendentes (se existir)
                const tbody = document.getElementById('corpoTabelaPendentes');
                if (tbody) {
                    if (!resultado.viagens_pendentes || !Array.isArray(resultado.viagens_pendentes) || resultado.viagens_pendentes.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="7" style="padding: 20px; text-align: center; color: var(--text-secondary);">Nenhum dado encontrado</td></tr>`;
                    } else {
                        tbody.innerHTML = resultado.viagens_pendentes.map(item => `
                            <tr style="border-bottom:1px solid var(--border-color);">
                                <td style="padding:12px; color:var(--text-primary);">${item.viagem}</td>
                                <td style="padding:12px; color:var(--text-primary);">${item.palete}</td>
                                <td style="padding:12px; color:var(--text-primary);">${item.prep || ''}</td>
                                <td style="padding:12px; color:var(--text-primary);">${item.lido || ''}</td>
                                <td style="padding:12px; color:var(--text-primary);">${item.total || ''}</td>
                            </tr>
                        `).join('');
                    }
                }
    } catch (e) {
        alert('Erro ao buscar dados de status prep: ' + e.message);
    }
}
window.carregarStatusPrep = carregarStatusPrep;
// Garantir funções globais para uso no HTML
if (typeof carregarStatusPrep !== 'undefined') window.carregarStatusPrep = carregarStatusPrep;
if (typeof carregarPaletesPreparados !== 'undefined') window.carregarPaletesPreparados = carregarPaletesPreparados;
// JS principal do projeto
console.log('main.js carregado');

function navegar(rota) {
    window.location.href = rota;
}

// Função global para adicionar viagem TRA
async function adicionarViagemTRA() {
    console.log('adicionarViagemTRA chamada');
    const numeroViagem = document.getElementById('numeroViagem').value.trim();
    const btnAdicionar = document.getElementById('btnAdicionarTRA');
    
    console.log('Botão encontrado:', btnAdicionar);
    console.log('Número da viagem:', numeroViagem);
    
    if (!numeroViagem) {
        alert('⚠️ Por favor, digite o número da viagem');
        return;
    }
    
    if (!/^\d+$/.test(numeroViagem)) {
        alert('⚠️ O número da viagem deve conter apenas dígitos');
        return;
    }
    
    const confirmacao = confirm(`Deseja converter a viagem TRA ${numeroViagem} para STD?`);
    if (!confirmacao) return;
    
    console.log('Iniciando requisição...');
    
    // Desabilitar botão e mostrar loading
    btnAdicionar.disabled = true;
    const textoOriginal = btnAdicionar.innerHTML;
    btnAdicionar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adicionando...';
    
    console.log('Botão atualizado para loading');
    
    try {
        const response = await fetch('/api/viagem/adicionar-tra', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                numero_viagem: numeroViagem
            })
        });
        
        const resultado = await response.json();
        
        if (resultado.success) {
            alert(`✅ ${resultado.message}\n${resultado.registros_atualizados} registro(s) atualizado(s)`);
            document.getElementById('numeroViagem').value = '';
            
            // Recarregar dados do dashboard
            const btnHoje = document.querySelector('#filtro-dashboard button:nth-of-type(2)');
            if (btnHoje) {
                btnHoje.click();
            }
        } else {
            alert(`❌ Erro: ${resultado.error}`);
        }
        
    } catch (error) {
        console.error('❌ Erro ao adicionar viagem:', error);
        alert(`❌ Erro ao adicionar viagem: ${error.message}`);
    } finally {
        console.log('Finalizando - restaurando botão');
        // Reabilitar botão
        btnAdicionar.disabled = false;
        btnAdicionar.innerHTML = '<i class="fas fa-plus"></i> Adicionar como STD';
        console.log('Botão restaurado');
    }
}

// Funções do Dashboard
if (document.getElementById('header-dashboard')) {
    // Atualizar relógio
    function atualizarRelogio() {
        const agora = new Date();
        const horas = String(agora.getHours()).padStart(2, '0');
        const minutos = String(agora.getMinutes()).padStart(2, '0');
        const segundos = String(agora.getSeconds()).padStart(2, '0');
        document.getElementById('currentTime').textContent = `${horas}:${minutos}:${segundos}`;
        
        const dias = ['domingo', 'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado'];
        const meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
        const diaSemana = dias[agora.getDay()];
        const dia = agora.getDate();
        const mes = meses[agora.getMonth()];
        const ano = agora.getFullYear();
        document.getElementById('currentDate').textContent = `${dia} de ${mes} de ${ano}`;
    }
    
    setInterval(atualizarRelogio, 1000);
    atualizarRelogio();
    
    // Função para formatar data YYYY-MM-DD para YYYYMMDD
    function formatarDataParaAPI(dataStr) {
        return dataStr.replace(/-/g, '');
    }
    
    // Função para buscar dados do dashboard
    async function buscarDadosDashboard() {
        const dataInicial = document.getElementById('dataInicial').value;
        const dataFinal = document.getElementById('dataFinal').value;
        const btnBuscar = document.querySelector('#filtro-dashboard button:first-of-type');
        
        if (!dataInicial || !dataFinal) {
            alert('Por favor, selecione as datas inicial e final.');
            return;
        }
        
        // Desabilitar botão durante busca
        btnBuscar.disabled = true;
        btnBuscar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Buscando...';
        
        try {
            const dataInicialFormatada = formatarDataParaAPI(dataInicial);
            const dataFinalFormatada = formatarDataParaAPI(dataFinal);
            
            const response = await fetch('/api/volumes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    data_inicial: dataInicialFormatada,
                    data_final: dataFinalFormatada
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                atualizarCardsDashboard(result.data);
                // Buscar peso pendente de extração
                buscarPesoPendenteExtracao(dataInicialFormatada, dataFinalFormatada);
            } else {
                alert('Erro ao buscar dados: ' + (result.error || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao buscar dados. Verifique o console para mais detalhes.');
        } finally {
            // Reabilitar botão
            btnBuscar.disabled = false;
            btnBuscar.innerHTML = '<i class="fas fa-search"></i> Buscar';
        }
    }
    
    // Função para buscar dados de hoje
    async function buscarDadosHoje() {
        const hoje = new Date();
        const ano = hoje.getFullYear();
        const mes = String(hoje.getMonth() + 1).padStart(2, '0');
        const dia = String(hoje.getDate()).padStart(2, '0');
        const dataFormatada = `${ano}-${mes}-${dia}`;
        document.getElementById('dataInicial').value = dataFormatada;
        document.getElementById('dataFinal').value = dataFormatada;
        buscarDadosDashboard();
    }
    
    // Atualizar os cards com os dados da API
    function atualizarCardsDashboard(data) {
        // Atualizar título com a data inicial
        const dataInicial = document.getElementById('dataInicial').value;
        if (dataInicial) {
            const partes = dataInicial.split('-');
            const dataFormatada = `${partes[2]}/${partes[1]}/${partes[0]}`;
            const tituloFaturamento = document.getElementById('tituloFaturamento');
            if (tituloFaturamento) {
                tituloFaturamento.textContent = `Faturamento ${dataFormatada}`;
            }
        }
        
        // Card principal: Volume Recebido (PEDIDO_X7)
        if (data.pedidos_x7 && data.pedidos_x7.success) {
            const totalPeso = data.pedidos_x7.total_peso || 0;
            const elemento = document.getElementById('valorPedidosX7');
            if (elemento) {
                elemento.textContent = totalPeso.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        
        // HET Preparado
        if (data.het && data.het.preparado !== undefined) {
            const elemento = document.getElementById('valorFeitoBatido');
            if (elemento) {
                elemento.textContent = data.het.preparado.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        
        // HET Pendente
        if (data.het && data.het.pendente !== undefined) {
            const elemento = document.getElementById('valorFaltaBatido');
            if (elemento) {
                elemento.textContent = data.het.pendente.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        
        // HOM Preparado
        if (data.hom && data.hom.preparado !== undefined) {
            const elemento = document.getElementById('valorHomBaixados');
            if (elemento) {
                elemento.textContent = data.hom.preparado.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        
        // HOM Pendente
        if (data.hom && data.hom.pendente !== undefined) {
            const elemento = document.getElementById('valorFaltaBaixar');
            if (elemento) {
                elemento.textContent = data.hom.pendente.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        
        // Volume Total (HET + HOM)
        if (data.consolidado && data.consolidado.total !== undefined) {
            const elemento = document.getElementById('valorVolumeDia');
            if (elemento) {
                elemento.textContent = data.consolidado.total.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        
        // Total Preparado (HET + HOM)
        if (data.consolidado && data.consolidado.preparado !== undefined) {
            const elemento = document.getElementById('valorFeitoTotal');
            if (elemento) {
                elemento.textContent = data.consolidado.preparado.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        
        // Total Pendente (HET + HOM)
        if (data.consolidado && data.consolidado.pendente !== undefined) {
            const elemento = document.getElementById('valorFaltaTotal');
            if (elemento) {
                elemento.textContent = data.consolidado.pendente.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
    }
    
    // Buscar Peso Pendente de Extração
    async function buscarPesoPendenteExtracao(dataInicial, dataFinal) {
        try {
            const response = await fetch('/api/peso-pendente-extracao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data_inicial: dataInicial,
                    data_final: dataFinal
                })
            });

            const resultado = await response.json();

            if (resultado.success) {
                const elemento = document.getElementById('valorPesoPendenteExtracao');
                if (elemento) {
                    elemento.textContent = resultado.total_toneladas.toLocaleString('pt-BR', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }
            }
        } catch (error) {
            console.error('Erro ao buscar peso pendente extração:', error);
        }
    }
    
    // Adicionar event listeners aos botões
    const btnBuscar = document.querySelector('#filtro-dashboard button:nth-of-type(1)');
    const btnHoje = document.querySelector('#filtro-dashboard button:nth-of-type(2)');
    const dataInicial = document.getElementById('dataInicial');
    const dataFinal = document.getElementById('dataFinal');
    
    if (btnBuscar) {
        btnBuscar.addEventListener('click', buscarDadosDashboard);
    }
    
    if (btnHoje) {
        btnHoje.addEventListener('click', buscarDadosHoje);
    }
    
    // Bloquear Enter específico nos campos de data
    if (dataInicial) {
        dataInicial.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                e.stopImmediatePropagation();
                return false;
            }
        }, true);
        
        // Ao selecionar data, move foco para próximo campo
        dataInicial.addEventListener('change', () => {
            if (dataFinal) {
                dataFinal.focus();
            }
        });
    }
    
    if (dataFinal) {
        dataFinal.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                e.stopImmediatePropagation();
                return false;
            }
        }, true);
        
        // Ao selecionar data final, remove foco e move para botão buscar
        dataFinal.addEventListener('change', () => {
            dataFinal.blur();
            if (btnBuscar) {
                btnBuscar.focus();
            }
        });
    }
    
    // Enter global para acionar busca em qualquer lugar da página
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            // Não acionar se estiver em textarea ou botão
            if (e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'BUTTON') {
                buscarDadosDashboard();
            }
        }
    });
    
    // Carregar dados de hoje automaticamente ao abrir a página
    window.addEventListener('load', buscarDadosHoje);
    
    // Função para exportar Excel do dashboard
    async function exportarExcelDashboard() {
        const dataInicial = document.getElementById('dataInicial').value;
        const dataFinal = document.getElementById('dataFinal').value;
        const btnExcel = document.querySelector('#filtro-dashboard button:nth-of-type(3)');
        
        if (!dataInicial || !dataFinal) {
            alert('⚠️ Por favor, selecione as datas inicial e final antes de exportar.');
            return;
        }
        
        // Desabilitar botão durante exportação
        btnExcel.disabled = true;
        const textoOriginal = btnExcel.innerHTML;
        btnExcel.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Gerando...';
        
        try {
            const response = await fetch('/api/exportar-dashboard-excel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    data_inicial: dataInicial,
                    data_final: dataFinal
                })
            });
            
            if (response.ok) {
                // Criar link de download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `dashboard_${dataInicial}_a_${dataFinal}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                // Mensagem de sucesso
                alert('✅ Excel exportado com sucesso!');
            } else {
                const errorData = await response.json();
                alert('❌ Erro ao exportar Excel: ' + (errorData.error || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('Erro ao exportar Excel:', error);
            alert('❌ Erro ao exportar Excel. Verifique o console para mais detalhes.');
        } finally {
            // Reabilitar botão
            btnExcel.disabled = false;
            btnExcel.innerHTML = textoOriginal;
        }
    }
    
    // Expor função globalmente para uso no HTML
    window.exportarExcelDashboard = exportarExcelDashboard;

    // ========================================
    // MODAIS HET E HOM PENDENTES
    // ========================================
    
    // Configurar eventos dos modais após DOM carregar
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            console.log('🔧 Configurando eventos dos modais...');
            
            // Card HET Pendente
            const cardHetPendente = document.getElementById('cardHetPendente');
            console.log('🎯 Card HET Pendente:', cardHetPendente);
            
            if (cardHetPendente) {
                cardHetPendente.addEventListener('click', abrirModalHetPendente);
                cardHetPendente.addEventListener('mouseenter', (e) => {
                    e.currentTarget.style.transform = 'translateY(-5px)';
                });
                cardHetPendente.addEventListener('mouseleave', (e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                });
                console.log('✅ Card HET Pendente configurado');
            }

            // Card HOM Pendente
            const cardHomPendente = document.getElementById('cardHomPendente');
            console.log('🎯 Card HOM Pendente:', cardHomPendente);
            
            if (cardHomPendente) {
                cardHomPendente.addEventListener('click', abrirModalHomPendente);
                cardHomPendente.addEventListener('mouseenter', (e) => {
                    e.currentTarget.style.transform = 'translateY(-5px)';
                });
                cardHomPendente.addEventListener('mouseleave', (e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                });
                console.log('✅ Card HOM Pendente configurado');
            }

            // Card Peso Pendente de Extração
            const cardPesoPendenteExtracao = document.getElementById('cardPesoPendenteExtracao');
            console.log('🎯 Card Peso Pendente Extração:', cardPesoPendenteExtracao);
            
            if (cardPesoPendenteExtracao) {
                cardPesoPendenteExtracao.addEventListener('click', abrirModalPesoPendenteExtracao);
                cardPesoPendenteExtracao.addEventListener('mouseenter', (e) => {
                    e.currentTarget.style.transform = 'translateY(-5px)';
                });
                cardPesoPendenteExtracao.addEventListener('mouseleave', (e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                });
                console.log('✅ Card Peso Pendente Extração configurado');
            }

            // Fechar modais ao clicar fora
            const modalHetPendente = document.getElementById('modalHetPendente');
            const modalHomPendente = document.getElementById('modalHomPendente');
            const modalPesoPendenteExtracao = document.getElementById('modalPesoPendenteExtracao');

            if (modalHetPendente) {
                modalHetPendente.addEventListener('click', (e) => {
                    if (e.target === modalHetPendente) {
                        modalHetPendente.style.display = 'none';
                    }
                });
            }

            if (modalHomPendente) {
                modalHomPendente.addEventListener('click', (e) => {
                    if (e.target === modalHomPendente) {
                        modalHomPendente.style.display = 'none';
                    }
                });
            }

            if (modalPesoPendenteExtracao) {
                modalPesoPendenteExtracao.addEventListener('click', (e) => {
                    if (e.target === modalPesoPendenteExtracao) {
                        modalPesoPendenteExtracao.style.display = 'none';
                    }
                });
            }

            // Fechar modais com ESC
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    if (modalHetPendente && modalHetPendente.style.display === 'block') {
                        modalHetPendente.style.display = 'none';
                    }
                    if (modalHomPendente && modalHomPendente.style.display === 'block') {
                        modalHomPendente.style.display = 'none';
                    }
                }
            });
        }, 1000);
    });

    // Abrir modal HET Pendente
    async function abrirModalHetPendente() {
        console.log('🖱️ Card HET Pendente clicado!');
        const modal = document.getElementById('modalHetPendente');
        if (!modal) return;

        modal.style.display = 'block';
        
        try {
            const dataInicial = document.getElementById('dataInicial')?.value || '';
            const dataFinal = document.getElementById('dataFinal')?.value || '';
            
            if (!dataInicial || !dataFinal) {
                alert('Por favor, selecione o período!');
                modal.style.display = 'none';
                return;
            }

            const dataInicialFormatada = dataInicial.replace(/-/g, '');
            const dataFinalFormatada = dataFinal.replace(/-/g, '');

            const response = await fetch('/api/het-pendentes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data_inicial: dataInicialFormatada,
                    data_final: dataFinalFormatada
                })
            });

            const resultado = await response.json();

            if (resultado.success) {
                if (resultado.total === 0) {
                    alert('✅ Nenhuma viagem HET pendente encontrada!');
                    modal.style.display = 'none';
                    return;
                }
                preencherTabelaHetPendente(resultado.dados, resultado.total, resultado.total_toneladas);
            } else {
                throw new Error(resultado.error || 'Erro ao buscar dados');
            }
        } catch (error) {
            console.error('Erro ao buscar HET pendentes:', error);
            const tbody = document.getElementById('corpoTabelaHetPendente');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="6" style="padding:20px; text-align:center; color:#ff4757;">Erro: ${error.message}</td></tr>`;
            }
        }
    }

    // Preencher tabela HET Pendente
    function preencherTabelaHetPendente(dados, total, toneladas) {
        const tbody = document.getElementById('corpoTabelaHetPendente');
        const totalElement = document.getElementById('hetPendentesTotal');
        const toneladasElement = document.getElementById('hetPendentesToneladas');

        if (totalElement) totalElement.textContent = total || 0;
        if (toneladasElement) toneladasElement.textContent = Number(toneladas || 0).toFixed(2);

        if (!tbody) return;

        if (!dados || dados.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="padding:20px; text-align:center; color:var(--text-secondary);">Nenhum item pendente</td></tr>`;
            return;
        }

        let html = '';
        dados.forEach(item => {
            const corPercentual = item.percentual >= 80 ? '#00d4ff' : item.percentual >= 50 ? '#ffaa00' : '#ff4757';
            html += `
                <tr style="border-bottom:1px solid var(--border-color);">
                    <td style="padding:12px; color:var(--text-primary);">${item.viagem || 'N/A'}</td>
                    <td style="padding:12px; color:var(--text-primary);">${item.palete || 'N/A'}</td>
                    <td style="padding:12px; color:var(--text-primary);">${item.esperado || 0}</td>
                    <td style="padding:12px; color:var(--text-primary);">${item.lido || 0}</td>
                    <td style="padding:12px; color:${corPercentual}; font-weight:600;">${(item.percentual || 0)}%</td>
                    <td style="padding:12px; color:var(--text-primary);">${Number(item.peso || 0).toFixed(4)}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }

    // Abrir modal HOM Pendente
    async function abrirModalHomPendente() {
        console.log('🖱️ Card HOM Pendente clicado!');
        const modal = document.getElementById('modalHomPendente');
        if (!modal) return;

        modal.style.display = 'block';
        
        try {
            const dataInicial = document.getElementById('dataInicial')?.value || '';
            const dataFinal = document.getElementById('dataFinal')?.value || '';
            
            if (!dataInicial || !dataFinal) {
                alert('Por favor, selecione o período!');
                modal.style.display = 'none';
                return;
            }

            const dataInicialFormatada = dataInicial.replace(/-/g, '');
            const dataFinalFormatada = dataFinal.replace(/-/g, '');

            const response = await fetch('/api/hom-pendentes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data_inicial: dataInicialFormatada,
                    data_final: dataFinalFormatada
                })
            });

            const resultado = await response.json();

            if (resultado.success) {
                if (resultado.total === 0) {
                    alert('✅ Nenhuma viagem HOM pendente encontrada!');
                    modal.style.display = 'none';
                    return;
                }
                preencherTabelaHomPendente(resultado.dados, resultado.total, resultado.total_toneladas);
            } else {
                throw new Error(resultado.error || 'Erro ao buscar dados');
            }
        } catch (error) {
            console.error('Erro ao buscar HOM pendentes:', error);
            const tbody = document.getElementById('corpoTabelaHomPendente');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="3" style="padding:20px; text-align:center; color:#ff4757;">Erro: ${error.message}</td></tr>`;
            }
        }
    }

    // Preencher tabela HOM Pendente
    function preencherTabelaHomPendente(dados, total, toneladas) {
        const tbody = document.getElementById('corpoTabelaHomPendente');
        const totalElement = document.getElementById('homPendentesTotal');
        const toneladasElement = document.getElementById('homPendentesToneladas');

        if (totalElement) totalElement.textContent = total || 0;
        if (toneladasElement) toneladasElement.textContent = Number(toneladas || 0).toFixed(2);

        if (!tbody) return;

        if (!dados || dados.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="padding:20px; text-align:center; color:var(--text-secondary);">Nenhum item pendente</td></tr>`;
            return;
        }

        let html = '';
        dados.forEach(item => {
            html += `
                <tr style="border-bottom:1px solid var(--border-color);">
                    <td style="padding:12px; color:var(--text-primary);">${item.viagem}</td>
                    <td style="padding:12px; color:var(--text-primary);">${item.palete || 'N/A'}</td>
                    <td style="padding:12px; color:var(--text-primary);">${Number(item.peso || 0).toFixed(4)}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }

    // Abrir modal Peso Pendente de Extração
    async function abrirModalPesoPendenteExtracao() {
        console.log('🖱️ Card Peso Pendente Extração clicado!');
        const modal = document.getElementById('modalPesoPendenteExtracao');
        if (!modal) return;

        modal.style.display = 'block';
        
        try {
            const dataInicial = document.getElementById('dataInicial')?.value || '';
            const dataFinal = document.getElementById('dataFinal')?.value || '';
            
            if (!dataInicial || !dataFinal) {
                alert('Por favor, selecione o período!');
                modal.style.display = 'none';
                return;
            }

            const dataInicialFormatada = dataInicial.replace(/-/g, '');
            const dataFinalFormatada = dataFinal.replace(/-/g, '');

            const response = await fetch('/api/peso-pendente-extracao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data_inicial: dataInicialFormatada,
                    data_final: dataFinalFormatada
                })
            });

            const resultado = await response.json();

            if (resultado.success) {
                if (resultado.total === 0) {
                    alert('✅ Nenhuma viagem pendente de extração encontrada!');
                    modal.style.display = 'none';
                    return;
                }
                preencherTabelaPesoPendenteExtracao(resultado.dados, resultado.total, resultado.total_toneladas);
            } else {
                throw new Error(resultado.error || 'Erro ao buscar dados');
            }
        } catch (error) {
            console.error('Erro ao buscar peso pendente extração:', error);
            const tbody = document.getElementById('corpoTabelaPesoPendenteExtracao');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="3" style="padding:20px; text-align:center; color:#ff4757;">Erro: ${error.message}</td></tr>`;
            }
        }
    }

    // Preencher tabela Peso Pendente de Extração
    function preencherTabelaPesoPendenteExtracao(dados, total, toneladas) {
        const tbody = document.getElementById('corpoTabelaPesoPendenteExtracao');
        const totalElement = document.getElementById('pesoPendenteExtracaoTotal');
        const toneladasElement = document.getElementById('pesoPendenteExtracaoToneladas');

        if (totalElement) totalElement.textContent = total || 0;
        if (toneladasElement) toneladasElement.textContent = Number(toneladas || 0).toFixed(2);

        if (!tbody) return;

        if (!dados || dados.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="padding:20px; text-align:center; color:var(--text-secondary);">Nenhum item pendente</td></tr>`;
            return;
        }

        let html = '';
        dados.forEach(item => {
            const dataStr = item.data_criacao;
            const dataFormatada = `${dataStr.substring(6, 8)}/${dataStr.substring(4, 6)}/${dataStr.substring(0, 4)}`;
            const viagemFormatada = parseInt(item.viagem); // Remove .0
            
            html += `
                <tr style="border-bottom:1px solid var(--border-color);">
                    <td style="padding:12px; color:var(--text-primary);">${viagemFormatada}</td>
                    <td style="padding:12px; color:var(--text-primary);">${Number(item.peso || 0).toFixed(4)}</td>
                    <td style="padding:12px; color:var(--text-secondary);">${dataFormatada}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }
}

