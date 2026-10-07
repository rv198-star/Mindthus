// Local reading controls only. No data mutation, storage, network or business actions.
(() => {
  document.body.classList.add('ready');
  const source = document.getElementById('source');
  document.querySelector('[data-action="theme"]')?.addEventListener('click', e => {
    const active = document.body.classList.toggle('dark');
    e.currentTarget.setAttribute('aria-pressed', String(active));
    e.currentTarget.textContent = active ? '浅色' : '深色';
  });
  document.querySelector('[data-action="reading"]')?.addEventListener('click', e => {
    const active = document.body.classList.toggle('reading');
    e.currentTarget.setAttribute('aria-pressed', String(active));
    e.currentTarget.textContent = active ? '分析布局' : '线性阅读';
  });
  document.querySelector('[data-action="source"]')?.addEventListener('click', () => {
    source.open = true;
    source.scrollIntoView({behavior:'auto',block:'start'});
    source.querySelector('summary').focus();
  });
  document.querySelector('[data-action="copy"]')?.addEventListener('click', async () => {
    const area = source.querySelector('textarea');
    const status = document.getElementById('copy-status');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('clipboard_unavailable');
      await navigator.clipboard.writeText(area.value);
      status.textContent = '原材料已复制。';
    } catch (_) {
      source.open = true;
      area.focus(); area.select();
      status.textContent = '浏览器未开放剪贴板，请复制已选中的原材料。';
    }
  });
  const table = document.querySelector('[data-work-table]');
  if (table) {
    const rows = [...table.querySelectorAll('tbody tr')];
    const filters = [...document.querySelectorAll('[data-filter]')];
    const input = document.querySelector('[data-search]');
    let filter = 'all';
    const apply = () => {
      const q = (input?.value || '').trim().toLocaleLowerCase();
      let count = 0;
      rows.forEach(row => {
        const show = (filter === 'all' || row.dataset.state === filter) && row.textContent.toLocaleLowerCase().includes(q);
        row.hidden = !show; if (show) count += 1;
      });
      document.getElementById('row-count').textContent = `${count} / ${rows.length} 项`;
      document.getElementById('empty').hidden = count > 0;
    };
    filters.forEach(button => button.addEventListener('click', () => {
      filter = button.dataset.filter;
      filters.forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      apply();
    }));
    input?.addEventListener('input', apply);
  }
  document.querySelectorAll('[data-ex-graph-size]').forEach(button => {
    button.addEventListener('click', () => {
      const scroll = button.closest('.ex-graph-shell').querySelector('.ex-graph-scroll');
      const active = scroll.classList.toggle('ex-natural');
      button.setAttribute('aria-pressed', String(active));
      button.textContent = active ? '适配全图' : '原始大小';
    });
  });
})();
