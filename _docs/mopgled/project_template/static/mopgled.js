/* # ╔═════════════════════════════════════════════════════════════════╗ */
/* # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ */
/* # ║  ▄█▛▘‾ ‾▝▜█▄  │ Mopgled – V1.0.1                               │║ */
/* # ║ ██▘       ▝██ │                                                │║ */
/* # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ */
/* # ║ ███▄_   _▄███ │ By Ir.On                                       │║ */
/* # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ */
/* # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:13         │║ */
/* # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ */
/* # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ */
/* # ║      ██    ▜▛ │ Caminho:                                       │║ */
/* # ║      ▜▛       │ _docs/mopgled/project_template/static/mopgl... │║ */
/* # ║               ├────────────────────────────────────────────────┤║ */
/* # ║               │ Detalhes:                                      │║ */
/* # ║               │ * V1.0.1 - [sem detalhes]                      │║ */
/* # ║               │                                                │║ */
/* # ║               └────────────────────────────────────────────────┘║ */
/* # ╚═════════════════════════════════════════════════════════════════╝ */


// MopGled js – app=11 vhash=dev-skip updated=2026-02-03 19:01:22.685576
// MopGled JS – 00 Base: tema e hooks globais
(function(){
  const THEME_KEY = "mopgled-theme";
  function applyTheme(mode){
    if(mode === "system"){
      document.body.removeAttribute("data-theme");
    } else {
      document.body.setAttribute("data-theme", mode);
    }
    localStorage.setItem(THEME_KEY, mode);
    document.querySelectorAll('[data-theme-mode]').forEach(input => {
      input.checked = input.value === mode;
    });
    const label = document.querySelector('[data-theme-label]');
    if(label){
      label.textContent = mode === "system" ? "Sistema" : (mode === "light" ? "Light" : "Dark");
    }
  }
  function initThemeToggle(){
    const initialTheme = localStorage.getItem(THEME_KEY) || "dark";
    applyTheme(initialTheme);
    document.querySelectorAll('[data-theme-mode]').forEach(input => {
      if(input.dataset.themeApply === "instant"){
        input.addEventListener('change', () => {
          applyTheme(input.value);
          document.querySelector('.theme-menu')?.classList.remove('open');
        });
      }
    });
    const themeBtn = document.querySelector('[data-theme-toggle]');
    if(themeBtn){
      themeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelector('.theme-menu')?.classList.toggle('open');
      });
      document.addEventListener('click', () => document.querySelector('.theme-menu')?.classList.remove('open'));
    }
  }
  document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
  });
})();
// MopGled JS – 01 Navegação: sidebar, tooltips e submenu
(function(){
  const COLLAPSED_CLASS = 'collapsed';
  function initSidebar(){
    const collapseBtn = document.getElementById('sidebarToggle');
    if(!collapseBtn) return;
    const updateIcon = () => {
      const isCollapsed = document.body.classList.contains(COLLAPSED_CLASS);
      collapseBtn.innerHTML = isCollapsed ? '<i class="bi bi-chevron-right"></i>' : '<i class="bi bi-chevron-left"></i>';
    };
    collapseBtn.addEventListener('click', () => {
      document.body.classList.toggle(COLLAPSED_CLASS);
      updateIcon();
    });
    updateIcon();
  }
  function initCollapsedTooltips(){
    const refreshTipY = (el) => {
      const rect = el.getBoundingClientRect();
      el.style.setProperty('--tooltip-y', `${rect.top + rect.height/2}px`);
    };
    document.querySelectorAll('.menu-item[data-tip], .item[data-tip]').forEach(item => {
      item.addEventListener('mouseenter', () => refreshTipY(item));
      item.addEventListener('focus', () => refreshTipY(item));
    });
  }
  function initSubmenu(){
    const btn = document.getElementById("submenuBtn");
    const box = document.getElementById("submenuBox");
    if(!btn || !box) return;
    btn.addEventListener("click", function(e){
      e.stopPropagation();
      box.classList.toggle("open");
      btn.classList.toggle("active");
      const rect = box.getBoundingClientRect();
      const overflow = rect.bottom - window.innerHeight + 16;
      box.style.top = overflow > 0 ? `calc(50% - ${overflow}px)` : "50%";
    });
    document.addEventListener("click", function(e){
      if(!box.contains(e.target) && !btn.contains(e.target)){
        box.classList.remove("open");
        btn.classList.remove("active");
        box.style.top = "50%";
      }
    });
  }
  document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initCollapsedTooltips();
    initSubmenu();
  });
})();
// MopGled JS – 02 Forms (placeholder para lógicas futuras)
(() => {
  // Reservado para validações/mascaras futuras.
})();
// MopGled JS – 03 Botões (placeholder)
(() => {
  // Espaço para interações específicas de botões.
})();
// MopGled JS – 04 Abas com overflow e setas
(function(){
  function initTabset(root){
    const strip = root.querySelector('.tabstrip, .mm-tabstrip');
    const prev = root.querySelector('.nav-prev');
    const next = root.querySelector('.nav-next');
    if(!strip || !prev || !next) return;
    const update = () => {
      const hasOverflow = strip.scrollWidth > strip.clientWidth + 2;
      root.classList.toggle('has-overflow', hasOverflow);
    };
    prev.addEventListener('click', () => strip.scrollBy({ left: -180, behavior: 'smooth' }));
    next.addEventListener('click', () => strip.scrollBy({ left: 180, behavior: 'smooth' }));
    window.addEventListener('resize', update);
    update();
    strip.addEventListener('click', (e) => {
      const link = e.target.closest('.tab, .mm-tab');
      if(!link) return;
      e.preventDefault();
      strip.querySelectorAll('.tab, .mm-tab').forEach(t => t.classList.remove('active'));
      link.classList.add('active');
    });
  }
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.mm-tabs, .tabs').forEach(initTabset);
  });
})();
// MopGled JS – 05 Tabelas: seleção e realce
(function(){
  function highlightRow(chk){
    const tr = chk.closest('tr');
    if(tr){
      tr.classList.toggle('row-selected', chk.checked);
    }
  }
  document.addEventListener('DOMContentLoaded', () => {
    const checkAll = document.getElementById('checkAll');
    const rowChecks = Array.from(document.querySelectorAll('.row-check'));
    if(checkAll){
      checkAll.addEventListener('change', () => {
        rowChecks.forEach(c => {
          c.checked = checkAll.checked;
          highlightRow(c);
        });
      });
    }
    rowChecks.forEach(c => c.addEventListener('change', () => highlightRow(c)));
  });
})();
// MopGled JS – 06 Alerts e Toasts
(function(){
  function initToast(){
    const toastEl = document.getElementById('toast');
    const trigger = document.getElementById('openToast');
    if(!toastEl || !trigger) return;
    const hideToast = () => {
      toastEl.classList.add('hiding');
      setTimeout(() => toastEl.classList.add('d-none'), 350);
    };
    trigger.addEventListener('click', () => {
      toastEl.classList.remove('d-none', 'hiding');
      clearTimeout(window._mopgledToastTimeout);
      window._mopgledToastTimeout = setTimeout(hideToast, 8000);
    });
    window.hideMopgledToast = hideToast;
  }
  function initAlerts(){
    const alerts = Array.from(document.querySelectorAll('#alerts-container .alert'));
    alerts.forEach((alert, i) => {
      setTimeout(() => {
        alert.style.opacity = 1;
        alert.style.transform = 'translateY(0) scale(1)';
      }, i * 300);
    });
  }
  document.addEventListener('DOMContentLoaded', () => {
    initToast();
    initAlerts();
  });
})();
// MopGled JS – 07 Modais/Lightbox (demo simplificado)
(function(){
  const items = [
    { src: 'https://picsum.photos/seed/mad1/1280/720', title: 'Rio nas pedras' },
    { src: 'https://picsum.photos/seed/mad2/1280/720', title: 'Torre clássica' },
    { src: 'https://picsum.photos/seed/mad3/1280/720', title: 'Canoas ao pôr do sol' }
  ];
  let index = 0;
  const box = () => document.getElementById('lightbox');
  const img = () => document.getElementById('lightbox-img');
  const cap = () => document.getElementById('lightbox-cap');
  function render(){
    const b = box();
    const i = img();
    const c = cap();
    if(!b || !i || !c) return;
    const item = items[index];
    i.src = item.src;
    c.textContent = item.title;
  }
  function open(i=0){
    index = i;
    render();
    const b = box();
    if(b) b.style.display = 'flex';
  }
  function close(e){
    if(!e || e.target.id === 'lightbox' || e.currentTarget === e.target){
      const b = box();
      if(b) b.style.display = 'none';
    }
  }
  function nav(delta, e){
    e?.stopPropagation();
    index = (index + delta + items.length) % items.length;
    render();
  }
  document.addEventListener('DOMContentLoaded', () => {
    if(typeof window !== 'undefined'){
      window.openLightbox = open;
      window.closeLightbox = close;
      window.navLightbox = nav;
    }
  });
})();
// MopGled JS – 08 Cards (placeholder)
(() => {
  // Espaço para interações específicas dos cards.
})();
// MopGled JS – 09 Gráficos (placeholder)
(() => {
  // Adapte aqui caso use libs de gráficos específicas.
})();
// MopGled JS – 10 Upload (dropzone básico)
(function(){
  function initDropzone({ dropzoneSelector, inputSelector, hoverClass = 'hover', onSelect }) {
    const dropzone = document.querySelector(dropzoneSelector);
    const input = document.querySelector(inputSelector);
    if (!dropzone || !input) return;
    const addHover = () => dropzone.classList.add(hoverClass, 'is-hover');
    const removeHover = () => dropzone.classList.remove(hoverClass, 'is-hover');
    dropzone.querySelector('button')?.addEventListener('click', () => input.click());
    ['dragenter', 'dragover'].forEach(ev =>
      dropzone.addEventListener(ev, e => {
        e.preventDefault();
        e.stopPropagation();
        addHover();
      })
    );
    ['dragleave', 'drop'].forEach(ev =>
      dropzone.addEventListener(ev, e => {
        e.preventDefault();
        e.stopPropagation();
        removeHover();
      })
    );
    dropzone.addEventListener('drop', e => {
      if (e.dataTransfer?.files?.length) {
        input.files = e.dataTransfer.files;
        onSelect?.(input.files[0], input.files);
      }
    });
    input.addEventListener('change', () => {
      if (input.files?.length) {
        onSelect?.(input.files[0], input.files);
      }
    });
  }
  if (typeof window !== 'undefined') {
    window.MopgledUpload = { initDropzone };
  }
})();

/*
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
*/
