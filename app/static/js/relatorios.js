(() => {
  document.querySelectorAll('[data-acao="visualizar-relatorio"]').forEach((botao) => {
    botao.addEventListener('click', () => {
      const titulo = botao.dataset.titulo || 'Relatório';
      const conteudo = botao.dataset.conteudo || '';
      const bloco = document.createElement('pre');
      bloco.className = 'text-start';
      bloco.style.whiteSpace = 'pre-wrap';
      bloco.style.maxHeight = '55vh';
      bloco.style.overflow = 'auto';
      bloco.textContent = conteudo;
      Swal.fire({ title: titulo, html: bloco.outerHTML, width: 850 });
    });
  });
})();
