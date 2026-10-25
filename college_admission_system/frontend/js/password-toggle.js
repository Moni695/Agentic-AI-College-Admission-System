(function addPasswordVisibilityControls() {
  function enhance() {
    document.querySelectorAll('input[type="password"]').forEach(input => {
      if (input.dataset.passwordToggleReady === 'true') return;
      input.dataset.passwordToggleReady = 'true';

      const group = document.createElement('div');
      group.className = 'input-group password-input-group';
      group.style.margin = '6px 0 16px';
      input.style.margin = '0';
      input.parentNode.insertBefore(group, input);
      group.appendChild(input);

      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'btn btn-outline-secondary password-toggle';
      toggle.style.minWidth = '88px';
      toggle.style.whiteSpace = 'nowrap';
      toggle.style.fontWeight = '600';
      toggle.style.backgroundColor = '#f1f5f9';
      toggle.style.color = '#102a43';
      toggle.textContent = '👁 Show';
      toggle.setAttribute('aria-label', 'Show password');
      toggle.title = 'Show password';
      toggle.addEventListener('click', () => {
        const showing = input.type === 'text';
        input.type = showing ? 'password' : 'text';
        toggle.textContent = showing ? '👁 Show' : '🙈 Hide';
        toggle.setAttribute('aria-label', `${showing ? 'Show' : 'Hide'} password`);
        toggle.title = `${showing ? 'Show' : 'Hide'} password`;
      });
      group.appendChild(toggle);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', enhance);
  else enhance();
})();
