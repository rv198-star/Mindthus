// Local component only; no document/body mutation, persistence or network.
(() => {
  const root = document.currentScript.closest('.ex-inline');
  if (!root) return;
  root.classList.add('ready');
  root.querySelectorAll('[data-ex-graph-size]').forEach(button => {
    button.textContent = '全图概览';
    button.setAttribute('aria-pressed', 'false');
    button.addEventListener('click', () => {
      const scroll = button.closest('.ex-graph-shell').querySelector('.ex-graph-scroll');
      const overview = scroll.classList.toggle('ex-overview');
      button.textContent = overview ? '清晰原尺寸' : '全图概览';
      button.setAttribute('aria-pressed', String(overview));
    });
  });
  root.querySelector('[data-copy-source]')?.addEventListener('click', async () => {
    const text = root.querySelector('[data-source-text]');
    const status = root.querySelector('[role="status"]');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('clipboard_unavailable');
      await navigator.clipboard.writeText(text.textContent);
      status.textContent = '原材料已复制。';
    } catch (_) {
      const range = document.createRange(); range.selectNodeContents(text);
      const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
      status.textContent = '剪贴板未开放，请复制已选中的原材料。';
    }
  });
})();
