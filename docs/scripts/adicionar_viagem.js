// Função global para adicionar viagem TRA
async function adicionarViagemTRN() {
  const numeroViagem = document.getElementById('numeroViagem').value.trim();
  
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
  
  try {
    // Mostrar loading
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    
    const response = await fetch('http://localhost:5000/api/viagem/adicionar-trn', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        numero_viagem: numeroViagem
      })
    });
    
    const resultado = await response.json();
    
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    
    if (resultado.success) {
      alert(`✅ ${resultado.message}\n${resultado.registros_atualizados} registro(s) atualizado(s)`);
      document.getElementById('numeroViagem').value = '';
      
      // Recarregar dados
      if (window.dashboard) {
        await window.dashboard.carregarDadosIniciais();
      }
    } else {
      alert(`❌ Erro: ${resultado.error}`);
    }
    
  } catch (error) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    
    console.error('❌ Erro ao adicionar viagem:', error);
    alert(`❌ Erro ao adicionar viagem: ${error.message}`);
  }
}

// Função global para exportar viagens para Excel
async function exportarViagens() {
  const dataInicial = document.getElementById('dataInicial').value;
  const dataFinal = document.getElementById('dataFinal').value;
  
  if (!dataInicial || !dataFinal) {
    alert('⚠️ Selecione o período (data inicial e final) antes de exportar');
    return;
  }
  
  try {
    // Mostrar loading
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
      loadingOverlay.style.display = 'flex';
      const loadingText = loadingOverlay.querySelector('.loading-text');
      if (loadingText) loadingText.textContent = 'Gerando arquivo Excel...';
    }
    
    const response = await fetch('http://localhost:5000/api/exportar-viagens', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data_inicial: dataInicial,
        data_final: dataFinal
      })
    });
    
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    
    if (!response.ok) {
      const erro = await response.json();
      alert(`❌ Erro: ${erro.error}`);
      return;
    }
    
    // Download do arquivo
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `viagens_${dataInicial}_a_${dataFinal}.xlsx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    console.log('✅ Arquivo Excel gerado com sucesso!');
    
  } catch (error) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    
    console.error('❌ Erro ao exportar viagens:', error);
    alert(`❌ Erro ao exportar: ${error.message}`);
  }
}
