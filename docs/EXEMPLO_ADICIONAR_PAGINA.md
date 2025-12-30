# 📋 Como Adicionar Novas Funcionalidades ao Site

## 🎯 Estrutura Pronta

O site agora está preparado para receber múltiplas funcionalidades através do **sistema de navegação por seções**.

### Seções Disponíveis:
- ✅ **Dashboard** (já implementado)
- 📊 **Produção** (estrutura pronta)
- ⏰ **Turnos** (estrutura pronta)
- ⚙️ **Equipamentos** (estrutura pronta)
- 📄 **Relatórios** (estrutura pronta)
- 🔔 **Alertas** (estrutura pronta)
- 🔧 **Configurações** (estrutura pronta)

---

## 🚀 Como Adicionar Seu Código em Uma Seção

### Passo 1: Escolha a Seção
Abra o arquivo `index.html` e localize a seção desejada:

```html
<!-- SEÇÃO: PRODUÇÃO -->
<div id="secao-producao" class="secao-conteudo" style="display: none;">
  <h2 style="color: var(--text-primary); margin-bottom: 2rem;">
    <i class="fas fa-industry"></i> Produção
  </h2>
  
  <!-- ADICIONE SEU CÓDIGO AQUI -->
  <div class="metric-card" style="padding: 2rem; text-align: center;">
    <p style="color: var(--text-secondary); font-size: 1.2rem;">📊 Área em desenvolvimento</p>
    <p style="color: var(--text-secondary); margin-top: 1rem;">Adicione seus códigos de produção aqui</p>
  </div>
  
</div>
```

### Passo 2: Substitua o Conteúdo

**Exemplo 1: Adicionar Gráfico de Produção**
```html
<div id="secao-producao" class="secao-conteudo" style="display: none;">
  <h2 style="color: var(--text-primary); margin-bottom: 2rem;">
    <i class="fas fa-industry"></i> Análise de Produção
  </h2>
  
  <!-- Seus cards de métricas -->
  <section class="metrics-grid">
    <div class="metric-card">
      <div class="metric-header">
        <h3>Eficiência</h3>
      </div>
      <div class="metric-content">
        <div class="metric-value">87%</div>
        <div class="metric-label">Taxa média</div>
      </div>
    </div>
  </section>
  
  <!-- Seu gráfico -->
  <section class="grafico-container">
    <canvas id="graficoProducao"></canvas>
  </section>
</div>
```

**Exemplo 2: Adicionar Tabela de Turnos**
```html
<div id="secao-turnos" class="secao-conteudo" style="display: none;">
  <h2 style="color: var(--text-primary); margin-bottom: 2rem;">
    <i class="fas fa-clock"></i> Gestão de Turnos
  </h2>
  
  <div class="metric-card" style="padding: 2rem;">
    <table style="width: 100%; color: var(--text-primary);">
      <thead>
        <tr>
          <th>Turno</th>
          <th>Horário</th>
          <th>Equipe</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody id="tabelaTurnos">
        <!-- Dados preenchidos via JavaScript -->
      </tbody>
    </table>
  </div>
</div>
```

---

## 🔌 Se Precisar de Backend (Python/Flask)

### Adicionar Novo Endpoint no `app.py`:

```python
@app.route('/api/producao/eficiencia', methods=['GET'])
def obter_eficiencia():
    try:
        data = request.args.get('data')
        
        # Sua query SQL
        query = """
            SELECT 
                TURNO,
                SUM(QUANTIDADE) as TOTAL
            FROM SUA_TABELA
            WHERE DATA = ?
            GROUP BY TURNO
        """
        
        with ibm_db.pconnect(conn_string, "", "") as conn:
            df = pd.read_sql(query, conn, params=[data])
            
        return jsonify({
            'success': True,
            'dados': df.to_dict('records')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Chamar do Frontend (JavaScript):

```javascript
async function carregarEficiencia() {
  try {
    const data = '2025-11-21';
    const response = await fetch(`http://localhost:5000/api/producao/eficiencia?data=${data}`);
    const resultado = await response.json();
    
    if (resultado.success) {
      // Atualizar interface
      document.getElementById('eficiencia').textContent = resultado.dados[0].TOTAL;
    }
  } catch (error) {
    console.error('Erro:', error);
  }
}
```

---

## 📁 Organização Recomendada

Se você tem **muitos códigos**, considere criar arquivos separados:

```
Site_dashboard_faturamento/
├── index.html              # Página principal
├── app.py                  # Backend Flask
├── script.js               # Dashboard principal
├── adicionar_viagem.js     # Funcionalidade TRA
├── producao.js            # 🆕 Código da seção Produção
├── turnos.js              # 🆕 Código da seção Turnos
├── relatorios.js          # 🆕 Código da seção Relatórios
└── styles.css             # Estilos
```

**Incluir no HTML:**
```html
<script src="producao.js"></script>
<script src="turnos.js"></script>
```

---

## 🎨 Classes CSS Disponíveis

Você pode reutilizar as classes já estilizadas:

### Cards de Métricas:
- `.metric-card` - Card padrão
- `.metric-card-destaque` - Card em destaque (maior)
- `.metric-header` - Cabeçalho do card
- `.metric-value` - Valor grande
- `.metric-label` - Legenda pequena

### Grid:
- `.metrics-grid` - Grid responsivo de cards

### Gráficos:
- `.grafico-container` - Container para gráficos Chart.js

### Botões:
- `background: var(--primary-color)` - Azul padrão
- `background: var(--success-color)` - Verde
- `background: var(--warning-color)` - Amarelo
- `background: var(--danger-color)` - Vermelho

### Cores:
- `var(--text-primary)` - Texto branco
- `var(--text-secondary)` - Texto cinza
- `var(--dark-bg)` - Fundo escuro
- `var(--card-bg)` - Fundo do card

---

## ✅ Checklist para Adicionar Nova Funcionalidade

1. ☐ Decidir em qual seção colocar (Produção, Turnos, etc.)
2. ☐ Abrir `index.html` e localizar `<div id="secao-XXXXX">`
3. ☐ Substituir conteúdo placeholder por seu código HTML
4. ☐ Se precisar de dados do backend:
   - ☐ Adicionar endpoint em `app.py`
   - ☐ Criar função JavaScript para buscar dados
5. ☐ Testar navegação clicando no menu lateral
6. ☐ Verificar no console do navegador se há erros

---

## 🆘 Exemplo Completo: Seção "Relatórios"

### 1. Backend (`app.py`):
```python
@app.route('/api/relatorios/lista', methods=['GET'])
def listar_relatorios():
    relatorios = [
        {'id': 1, 'nome': 'Relatório de Produção', 'data': '2025-11-20'},
        {'id': 2, 'nome': 'Relatório de Qualidade', 'data': '2025-11-19'}
    ]
    return jsonify({'success': True, 'relatorios': relatorios})
```

### 2. Frontend (`index.html`):
```html
<div id="secao-relatorios" class="secao-conteudo" style="display: none;">
  <h2 style="color: var(--text-primary); margin-bottom: 2rem;">
    <i class="fas fa-file-alt"></i> Relatórios Disponíveis
  </h2>
  
  <div class="metric-card" style="padding: 2rem;">
    <div id="listaRelatorios">
      <!-- Preenchido via JavaScript -->
    </div>
  </div>
</div>
```

### 3. JavaScript (criar `relatorios.js`):
```javascript
async function carregarRelatorios() {
  try {
    const response = await fetch('http://localhost:5000/api/relatorios/lista');
    const dados = await response.json();
    
    if (dados.success) {
      const container = document.getElementById('listaRelatorios');
      container.innerHTML = dados.relatorios.map(r => `
        <div style="padding: 1rem; border-bottom: 1px solid #333;">
          <h3>${r.nome}</h3>
          <p>Data: ${r.data}</p>
          <button onclick="baixarRelatorio(${r.id})">📥 Baixar</button>
        </div>
      `).join('');
    }
  } catch (error) {
    console.error('Erro ao carregar relatórios:', error);
  }
}

// Chamar quando navegar para a seção
document.addEventListener('DOMContentLoaded', () => {
  // Detectar quando seção de relatórios é aberta
  const observer = new MutationObserver(() => {
    const secao = document.getElementById('secao-relatorios');
    if (secao && secao.style.display !== 'none') {
      carregarRelatorios();
    }
  });
  
  observer.observe(document.getElementById('secao-relatorios'), {
    attributes: true,
    attributeFilter: ['style']
  });
});
```

---

## 🎯 Próximos Passos

1. **Escolha a funcionalidade** que quer adicionar
2. **Copie o código** para a seção apropriada
3. **Teste navegando** pelo menu lateral
4. **Adicione backend** se necessário (SQL, APIs)

💡 **Dica:** Comece simples! Adicione primeiro um card estático, depois adicione dados dinâmicos.
