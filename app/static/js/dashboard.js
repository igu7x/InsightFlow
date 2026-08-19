(() => {
  const dados = document.getElementById('dashboardData');
  if (!dados || typeof Chart === 'undefined') return;

  const ler = (chave) => {
    try { return JSON.parse(dados.dataset[chave] || '[]'); } catch { return []; }
  };

  const departamentos = ler('departamentos');
  const totais = ler('totais');
  const atrasados = ler('atrasados');
  const status = ler('status');

  const graficoDepartamentos = document.getElementById('departamentosChart');
  if (graficoDepartamentos) {
    new Chart(graficoDepartamentos, {
      type: 'bar',
      data: {
        labels: departamentos,
        datasets: [
          { label: 'Total', data: totais, borderRadius: 8 },
          { label: 'Atrasados', data: atrasados, borderRadius: 8 },
        ],
      },
      options: {
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  const graficoStatus = document.getElementById('statusChart');
  if (graficoStatus) {
    new Chart(graficoStatus, {
      type: 'doughnut',
      data: {
        labels: ['Concluídos', 'Em andamento', 'Atrasados'],
        datasets: [{ data: status, borderWidth: 0 }],
      },
      options: { cutout: '68%', plugins: { legend: { position: 'bottom' } } },
    });
  }

  const limpar = document.getElementById('limparFiltros');
  if (limpar) {
    limpar.addEventListener('click', () => { window.location.href = '/dashboard'; });
  }
})();
