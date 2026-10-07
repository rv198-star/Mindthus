(() => {
  const root = document.currentScript.closest('.ex-root');
  if (!root) return;
  root.classList.add('ex-enhanced');
  const button = (action) => root.querySelector(`[data-ex-action="${action}"]`);
  const layout = button('layout');
  const dark = button('dark');
  layout?.addEventListener('click', () => {
    const doc = root.dataset.layout === 'doc';
    root.dataset.layout = doc ? 'sheet' : 'doc';
    layout.setAttribute('aria-pressed', String(!doc));
  });
  dark?.addEventListener('click', () => {
    const enabled = root.dataset.mode !== 'dark';
    root.dataset.mode = enabled ? 'dark' : 'light';
    dark.setAttribute('aria-pressed', String(enabled));
  });
  button('expand')?.addEventListener('click', () => {
    const details = [...root.querySelectorAll('details.ex-panel')];
    const open = details.some(d => !d.open);
    details.forEach(d => { d.open = open; });
    button('expand').setAttribute('aria-pressed', String(open));
  });
  root.querySelectorAll('[data-ex-graph-size]').forEach(control => {
    control.addEventListener('click', () => {
      const scroll = control.closest('.ex-graph-shell')?.querySelector('.ex-graph-scroll');
      if (!scroll) return;
      const natural = !scroll.classList.contains('ex-natural');
      scroll.classList.toggle('ex-natural', natural);
      control.setAttribute('aria-pressed', String(natural));
      control.textContent = natural ? control.dataset.fitLabel : control.dataset.naturalLabel;
    });
  });
  const copy = button('copy');
  copy?.addEventListener('click', async () => {
    const data = root.querySelector('[data-explain-source="v2"]');
    const view = root.querySelector('.ex-source-view');
    const area = view?.querySelector('textarea');
    const status = root.querySelector('.ex-status');
    try {
      const source = JSON.parse(data.textContent).source;
      if (!navigator.clipboard?.writeText) throw new Error('clipboard_unavailable');
      await navigator.clipboard.writeText(source);
      status.textContent = root.dataset.lang.startsWith('zh') ? '已复制本页源稿。' : 'Source copied.';
    } catch (_) {
      if (view && area) { view.open = true; area.focus(); area.select(); }
      if (status) status.textContent = root.dataset.lang.startsWith('zh') ? '请选择并复制下方源稿。' : 'Select and copy the source below.';
    }
  });
})();
