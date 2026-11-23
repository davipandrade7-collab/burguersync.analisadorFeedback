// BurgerSync Admin Dashboard
document.addEventListener('DOMContentLoaded', () => {
  let allFeedbacks = [];

  const container = document.getElementById('feedbacksContainer');
  const searchInput = document.getElementById('searchInput');
  const filterSentiment = document.getElementById('filterSentiment');
  const filterStatus = document.getElementById('filterStatus');
  const sortOrder = document.getElementById('sortOrder');
  const refreshBtn = document.getElementById('refreshBtn');
  const refreshIcon = document.getElementById('refreshIcon');
  const filteredCountBadge = document.getElementById('filteredCountBadge');

  // Metric elements
  const metricTotal = document.getElementById('metricTotal');
  const metricPositivos = document.getElementById('metricPositivos');
  const metricPositivosPct = document.getElementById('metricPositivosPct');
  const metricNeutros = document.getElementById('metricNeutros');
  const metricNeutrosPct = document.getElementById('metricNeutrosPct');
  const metricCriticos = document.getElementById('metricCriticos');
  const metricCriticosPct = document.getElementById('metricCriticosPct');
  const metricCriticosPendentesBadge = document.getElementById('metricCriticosPendentesBadge');

  // Load Feedbacks from API
  async function loadFeedbacks() {
    refreshIcon.classList.add('animate-spin');
    try {
      const response = await fetch('/api/feedbacks');
      if (!response.ok) throw new Error('Falha ao carregar feedbacks');
      allFeedbacks = await response.json();
      updateMetrics();
      renderList();
    } catch (err) {
      console.error(err);
      container.innerHTML = `
        <div class="p-8 text-center text-red-400 text-xs">
          Erro ao carregar dados do servidor. Certifique-se de que o backend está ativo.
        </div>
      `;
    } finally {
      setTimeout(() => refreshIcon.classList.remove('animate-spin'), 400);
    }
  }

  // Update KPI Metrics
  function updateMetrics() {
    const total = allFeedbacks.length;
    const positivos = allFeedbacks.filter(f => f.sentimento === 'Positivo').length;
    const neutros = allFeedbacks.filter(f => f.sentimento === 'Neutro').length;
    const criticos = allFeedbacks.filter(f => f.sentimento === 'Crítico').length;
    const criticosPendentes = allFeedbacks.filter(f => f.sentimento === 'Crítico' && f.status === 'pendente').length;

    metricTotal.textContent = total;
    metricPositivos.textContent = positivos;
    metricNeutros.textContent = neutros;
    metricCriticos.textContent = criticos;

    const calcPct = (val) => total > 0 ? `(${Math.round((val / total) * 100)}%)` : '(0%)';

    metricPositivosPct.textContent = calcPct(positivos);
    metricNeutrosPct.textContent = calcPct(neutros);
    metricCriticosPct.textContent = calcPct(criticos);

    if (criticosPendentes > 0) {
      metricCriticosPendentesBadge.textContent = `${criticosPendentes} PENDENTES`;
      metricCriticosPendentesBadge.classList.remove('hidden');
    } else {
      metricCriticosPendentesBadge.classList.add('hidden');
    }
  }

  // Toggle status (pendente <-> tratado)
  async function toggleStatus(id, currentStatus) {
    const newStatus = currentStatus === 'tratado' ? 'pendente' : 'tratado';
    try {
      const response = await fetch(`/api/feedbacks/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (!response.ok) throw new Error('Falha ao atualizar status');

      // Update locally
      const item = allFeedbacks.find(f => f.id === id);
      if (item) {
        item.status = newStatus;
        updateMetrics();
        renderList();
      }
    } catch (err) {
      alert('Erro ao atualizar status: ' + err.message);
    }
  }

  // Filter & Render
  function renderList() {
    const query = searchInput.value.toLowerCase().trim();
    const sentiment = filterSentiment.value;
    const status = filterStatus.value;
    const sort = sortOrder.value;

    let filtered = allFeedbacks.filter(item => {
      // Sentiment filter
      if (sentiment !== 'todos' && item.sentimento !== sentiment) return false;
      // Status filter
      if (status !== 'todos' && item.status !== status) return false;
      // Search query
      if (query) {
        const textToSearch = [
          item.cliente?.nome,
          item.cliente?.contato,
          item.cliente?.pedido_id,
          item.comentario,
          item.resumo,
          ...(item.tags || [])
        ].filter(Boolean).join(' ').toLowerCase();

        if (!textToSearch.includes(query)) return false;
      }
      return true;
    });

    // Sorting
    filtered.sort((a, b) => {
      if (sort === 'critico-primeiro') {
        const score = (val) => val === 'Crítico' ? 3 : (val === 'Neutro' ? 2 : 1);
        const scoreDiff = score(b.sentimento) - score(a.sentimento);
        if (scoreDiff !== 0) return scoreDiff;
        return new Date(b.criado_em) - new Date(a.criado_em);
      } else if (sort === 'antigo') {
        return new Date(a.criado_em) - new Date(b.criado_em);
      } else {
        // Recente default
        return new Date(b.criado_em) - new Date(a.criado_em);
      }
    });

    filteredCountBadge.textContent = `${filtered.length} exibidos`;

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="p-12 text-center text-stone-500 text-xs">
          Nenhuma avaliação encontrada com os filtros selecionados.
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(item => {
      const isTratado = item.status === 'tratado';
      const isCritico = item.sentimento === 'Crítico';
      const isPositivo = item.sentimento === 'Positivo';

      let sentimentBadgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
      if (isPositivo) sentimentBadgeClass = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      if (isCritico) sentimentBadgeClass = 'bg-red-500/10 text-red-400 border border-red-500/20';

      const dataFormatada = item.criado_em
        ? new Date(item.criado_em).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
        : 'Recente';

      return `
        <div class="p-5 hover:bg-stone-850/50 transition-colors ${isTratado ? 'opacity-65' : ''}">
          <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            
            <!-- Left: Checkbox & Main Info -->
            <div class="flex items-start gap-3.5 flex-grow">
              <!-- Checkbox -->
              <div class="pt-0.5">
                <input type="checkbox"
                  ${isTratado ? 'checked' : ''}
                  data-id="${item.id}"
                  data-status="${item.status}"
                  class="status-checkbox w-4 h-4 rounded border-stone-700 bg-stone-900 text-amber-500 focus:ring-amber-500 cursor-pointer"
                  title="Marcar como ${isTratado ? 'Pendente' : 'Tratado'}">
              </div>

              <!-- Content -->
              <div class="space-y-2 flex-grow">
                <!-- Header with Client & Sentiment -->
                <div class="flex flex-wrap items-center gap-2">
                  <span class="font-bold text-sm text-stone-100">${escapeHtml(item.cliente?.nome || 'Cliente Anônimo')}</span>
                  
                  <span class="text-xs px-2 py-0.5 rounded-full font-medium ${sentimentBadgeClass}">
                    ${item.sentimento || 'Neutro'}
                  </span>

                  ${isCritico && item.alerta_disparado ? `
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-red-950/80 text-red-300 border border-red-800 flex items-center gap-1 font-semibold">
                      <span class="w-1.5 h-1.5 rounded-full bg-red-400"></span> Alerta de Crise Disparado
                    </span>
                  ` : ''}

                  <span class="text-xs text-stone-500 ml-auto">${dataFormatada}</span>
                </div>

                <!-- Contact & Order -->
                <div class="text-xs text-stone-400 flex flex-wrap items-center gap-x-4 gap-y-1">
                  <span><strong class="text-stone-500">Contato:</strong> ${escapeHtml(item.cliente?.contato || 'Não informado')}</span>
                  <span><strong class="text-stone-500">Pedido:</strong> <code class="text-amber-400/90 font-mono text-[11px]">${escapeHtml(item.cliente?.pedido_id || 'N/A')}</code></span>
                  <span><strong class="text-stone-500">Status:</strong> <span class="capitalize ${isTratado ? 'text-emerald-400' : 'text-amber-400'} font-semibold">${item.status || 'pendente'}</span></span>
                </div>

                <!-- Comment -->
                <p class="text-xs text-stone-200 bg-stone-950/60 p-3 rounded-xl border border-stone-850 leading-relaxed">
                  "${escapeHtml(item.comentario)}"
                </p>

                <!-- AI Summary -->
                ${item.resumo ? `
                  <div class="text-[11px] text-stone-400 flex items-center gap-1.5">
                    <span class="text-amber-500 font-semibold">Resumo IA:</span>
                    <span>${escapeHtml(item.resumo)}</span>
                  </div>
                ` : ''}

                <!-- Tags -->
                <div class="flex flex-wrap items-center gap-1.5 pt-1">
                  <span class="text-[10px] text-stone-500 uppercase tracking-wider font-semibold">Tags:</span>
                  ${(item.tags || []).map(tag => `
                    <span class="text-[11px] px-2 py-0.5 rounded bg-stone-800 text-stone-300 border border-stone-750">
                      #${escapeHtml(tag)}
                    </span>
                  `).join('')}
                </div>
              </div>
            </div>

          </div>
        </div>
      `;
    }).join('');

    // Attach event listeners to checkboxes
    document.querySelectorAll('.status-checkbox').forEach(cb => {
      cb.addEventListener('change', (e) => {
        const id = e.target.dataset.id;
        const currentStatus = e.target.dataset.status;
        toggleStatus(id, currentStatus);
      });
    });
  }

  function escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Event Listeners
  searchInput.addEventListener('input', renderList);
  filterSentiment.addEventListener('change', renderList);
  filterStatus.addEventListener('change', renderList);
  sortOrder.addEventListener('change', renderList);
  refreshBtn.addEventListener('click', loadFeedbacks);

  // Initial load
  loadFeedbacks();

  // Auto-refresh every 30 seconds
  setInterval(loadFeedbacks, 30000);
});
