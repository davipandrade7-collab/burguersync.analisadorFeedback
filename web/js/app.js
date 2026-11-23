// Customer Feedback Form Handling
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('feedbackForm');
  const submitBtn = document.getElementById('submitBtn');
  const btnText = document.getElementById('btnText');
  const btnSpinner = document.getElementById('btnSpinner');
  const comentario = document.getElementById('comentario');
  const charCounter = document.getElementById('charCounter');
  const resultCard = document.getElementById('resultCard');
  const resetFormBtn = document.getElementById('resetFormBtn');

  // Star Rating elements
  const starBtns = document.querySelectorAll('.star-btn');
  const ratingScoreInput = document.getElementById('ratingScore');
  const starRatingLabel = document.getElementById('starRatingLabel');

  let currentRating = 5;

  const ratingDescriptions = {
    1: '1 estrela - Muito insatisfeito',
    2: '2 estrelas - Regular/Abaixo do esperado',
    3: '3 estrelas - Razoável',
    4: '4 estrelas - Muito bom',
    5: '5 estrelas - Excelente!'
  };

  function updateStars(score) {
    currentRating = score;
    ratingScoreInput.value = score;
    starBtns.forEach(btn => {
      const btnScore = parseInt(btn.dataset.score);
      if (btnScore <= score) {
        btn.classList.add('text-amber-400');
        btn.classList.remove('text-stone-600');
      } else {
        btn.classList.remove('text-amber-400');
        btn.classList.add('text-stone-600');
      }
    });
    starRatingLabel.textContent = ratingDescriptions[score] || `${score} estrelas`;
  }

  starBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      updateStars(parseInt(btn.dataset.score));
    });
    btn.addEventListener('mouseenter', () => {
      const score = parseInt(btn.dataset.score);
      starBtns.forEach(b => {
        if (parseInt(b.dataset.score) <= score) {
          b.classList.add('text-amber-300');
        } else {
          b.classList.remove('text-amber-300');
        }
      });
    });
    btn.addEventListener('mouseleave', () => {
      starBtns.forEach(b => b.classList.remove('text-amber-300'));
      updateStars(currentRating);
    });
  });

  // Default to 5 stars
  updateStars(5);

  // Character counter
  comentario.addEventListener('input', () => {
    charCounter.textContent = `${comentario.value.length} caracteres`;
  });

  // Reset form
  resetFormBtn.addEventListener('click', () => {
    form.reset();
    updateStars(5);
    charCounter.textContent = '0 caracteres';
    resultCard.classList.add('hidden');
    form.classList.remove('hidden');
  });

  // Submit handler
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const nome = document.getElementById('clienteNome').value.trim();
    const contato = document.getElementById('clienteContato').value.trim();
    const pedidoId = document.getElementById('pedidoId').value.trim();
    const textoComentario = comentario.value.trim();
    const nota = parseInt(ratingScoreInput.value);

    if (!nome || !contato || !textoComentario) {
      alert('Por favor, preencha os campos obrigatórios (*).');
      return;
    }

    // Set loading state
    submitBtn.disabled = true;
    btnText.textContent = 'Analisando com IA...';
    btnSpinner.classList.remove('hidden');

    try {
      const response = await fetch('/api/feedbacks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          cliente: {
            nome: nome,
            contato: contato,
            pedido_id: pedidoId || 'N/A'
          },
          comentario: textoComentario,
          nota: nota
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Falha ao processar avaliação.');
      }

      const result = await response.json();

      // Display results
      form.classList.add('hidden');
      resultCard.classList.remove('hidden');

      const badge = document.getElementById('resultSentimentBadge');
      const icon = document.getElementById('resultIcon');
      const tagsContainer = document.getElementById('resultTags');
      const summaryText = document.getElementById('resultSummary');

      // Style badge based on sentiment
      const sentiment = result.sentimento || 'Neutro';
      badge.textContent = sentiment;
      tagsContainer.innerHTML = '';

      if (sentiment === 'Positivo') {
        badge.className = 'font-semibold px-2.5 py-0.5 rounded-full text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        icon.className = 'w-10 h-10 rounded-full flex items-center justify-center text-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
        icon.textContent = '🌟';
        document.getElementById('resultTitle').textContent = 'Ficamos muito felizes!';
        document.getElementById('resultSubtitle').textContent = 'Seu feedback positivo impulsiona nossa equipe.';
      } else if (sentiment === 'Crítico') {
        badge.className = 'font-semibold px-2.5 py-0.5 rounded-full text-xs bg-red-500/20 text-red-400 border border-red-500/30';
        icon.className = 'w-10 h-10 rounded-full flex items-center justify-center text-xl bg-red-500/10 text-red-400 border border-red-500/20';
        icon.textContent = '⚠️';
        document.getElementById('resultTitle').textContent = 'Lamentamos pelo ocorrido!';
        document.getElementById('resultSubtitle').textContent = 'Nossa gerência em Ourinhos foi notificada imediatamente para resolver.';
      } else {
        badge.className = 'font-semibold px-2.5 py-0.5 rounded-full text-xs bg-amber-500/20 text-amber-400 border border-amber-500/30';
        icon.className = 'w-10 h-10 rounded-full flex items-center justify-center text-xl bg-amber-500/10 text-amber-400 border border-amber-500/20';
        icon.textContent = '💬';
        document.getElementById('resultTitle').textContent = 'Agradecemos sua colaboração!';
        document.getElementById('resultSubtitle').textContent = 'Seus comentários nos ajudam a aperfeiçoar nossos lanches.';
      }

      (result.tags || []).forEach(tag => {
        const tagSpan = document.createElement('span');
        tagSpan.className = 'px-2 py-0.5 rounded bg-stone-800 text-stone-300 border border-stone-700 text-[10px] font-medium';
        tagSpan.textContent = tag;
        tagsContainer.appendChild(tagSpan);
      });

      summaryText.textContent = `"${result.resumo || result.comentario}"`;

    } catch (err) {
      console.error('Erro:', err);
      alert('Houve um problema ao enviar seu feedback: ' + err.message);
    } finally {
      submitBtn.disabled = false;
      btnText.textContent = 'Enviar Feedback';
      btnSpinner.classList.add('hidden');
    }
  });
});
