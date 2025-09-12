let scrollPosition = 0;

document.addEventListener('DOMContentLoaded', () => {
  // --- Seletores dos Elementos Principais ---
  const body = document.body;
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  const desktopToggle = document.querySelector('.desktop-toggle');
  const mobileToggle = document.querySelector('.mobile-toggle');
  const overlay = document.getElementById('overlay');
  const submenuToggles = document.querySelectorAll('.submenu-toggle');

  // Se os elementos essenciais não existirem, não faz nada.
  if (!sidebar || !mainContent) return;

  // --- Funções de Controle do Menu ---

  // Controla o menu no DESKTOP (colapsado/expandido)
  const toggleDesktopSidebar = () => {
    sidebar.classList.toggle('collapsed');
    // Não salva mais o estado no localStorage - sempre abre quando clicado em uma opção
  };

  // NOVA FUNÇÃO: Sempre expande o sidebar quando uma opção é clicada
  const expandSidebarOnItemClick = () => {
    if (window.innerWidth > 768 && sidebar.classList.contains('collapsed')) {
      sidebar.classList.remove('collapsed');
    }
  };

  // Abre o menu no MOBILE
  const openMobileSidebar = () => {
    // Salva a posição atual do scroll da página
    scrollPosition = window.scrollY;

    // Aplica estilos ao body para "congelar" a página no lugar certo
    body.style.overflow = 'hidden';
    body.style.position = 'fixed';
    body.style.top = `-${scrollPosition}px`;
    body.style.width = '100%';

    // Abre o sidebar
    sidebar.classList.add('open');
    overlay.classList.add('active');
    mobileToggle.classList.add('active');
  };

  // Fecha o menu no MOBILE
  const closeMobileSidebar = () => {
    // Remove os estilos que "congelam" o body
    body.style.removeProperty('overflow');
    body.style.removeProperty('position');
    body.style.removeProperty('top');
    body.style.removeProperty('width');

    // Restaura a posição do scroll para onde estava
    window.scrollTo(0, scrollPosition);

    // Fecha o sidebar
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
    mobileToggle.classList.remove('active');
  };
  
  // NOVA FUNÇÃO: Controla submenu com comportamento especial para sidebar colapsado
  const toggleSubmenu = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const parentMenuItem = e.currentTarget.closest('.has-submenu');
    if (!parentMenuItem) return;

    // Se o sidebar estiver colapsado, expande primeiro
    if (sidebar.classList.contains('collapsed')) {
      sidebar.classList.remove('collapsed');
      // Aguarda a animação do sidebar antes de abrir o submenu
      setTimeout(() => {
        parentMenuItem.classList.add('open');
      }, 200);
    } else {
      parentMenuItem.classList.toggle('open');
    }
  };

  // NOVA FUNÇÃO: Cria tooltip para submenu quando sidebar está colapsado
  const createSubmenuTooltip = (submenuElement, parentElement) => {
    const tooltip = document.createElement('div');
    tooltip.className = 'submenu-tooltip';
    
    const submenuItems = submenuElement.querySelectorAll('.submenu-item');
    submenuItems.forEach(item => {
      const clonedItem = item.cloneNode(true);
      tooltip.appendChild(clonedItem);
    });
    
    parentElement.appendChild(tooltip);
    return tooltip;
  };

  // NOVA FUNÇÃO: Gerencia tooltips para submenus colapsados
  const setupSubmenuTooltips = () => {
    const hasSubmenuItems = document.querySelectorAll('.has-submenu');
    
    hasSubmenuItems.forEach(item => {
      const submenu = item.querySelector('.submenu');
      if (!submenu) return;

      // Remove tooltip existente se houver
      const existingTooltip = item.querySelector('.submenu-tooltip');
      if (existingTooltip) {
        existingTooltip.remove();
      }

      // Cria novo tooltip apenas se sidebar estiver colapsado
      if (sidebar.classList.contains('collapsed')) {
        const tooltip = createSubmenuTooltip(submenu, item);
        
        // Adiciona eventos para mostrar/esconder tooltip
        item.addEventListener('mouseenter', () => {
          if (sidebar.classList.contains('collapsed')) {
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
            tooltip.style.transform = 'translateX(0)';
          }
        });
        
        item.addEventListener('mouseleave', () => {
          tooltip.style.opacity = '0';
          tooltip.style.visibility = 'hidden';
          tooltip.style.transform = 'translateX(-10px)';
        });

        // Adiciona eventos aos links do tooltip
        const tooltipLinks = tooltip.querySelectorAll('a');
        tooltipLinks.forEach(link => {
          link.addEventListener('click', (e) => {
            // Expande o sidebar quando um item do submenu é clicado
            if (sidebar.classList.contains('collapsed')) {
              expandSidebarOnItemClick();
            }
          });
        });
      }
    });
  };

  // --- Lógica de Inicialização ---

  // 1. NÃO aplica mais o estado salvo automaticamente - sempre começa expandido
  // (Comentado: não queremos mais manter o estado)
  // if (window.innerWidth > 768 && localStorage.getItem('sidebarState') === 'collapsed') {
  //   sidebar.classList.add('collapsed');
  // }

  // 2. Configura tooltips iniciais
  setupSubmenuTooltips();

  // 3. Observer para detectar mudanças de classe no sidebar
  const sidebarObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'class') {
        setupSubmenuTooltips();
      }
    });
  });
  
  sidebarObserver.observe(sidebar, { attributes: true, attributeFilter: ['class'] });

  // 4. Adiciona os event listeners
  if (desktopToggle) {
    desktopToggle.addEventListener('click', toggleDesktopSidebar);
  }
  
  if (mobileToggle) {
    mobileToggle.addEventListener('click', () => {
      // Decide se abre ou fecha baseado na classe 'open'
      if (sidebar.classList.contains('open')) {
        closeMobileSidebar();
      } else {
        openMobileSidebar();
      }
    });
  }
  
  if (overlay) {
    overlay.addEventListener('click', closeMobileSidebar);
  }

  submenuToggles.forEach(toggle => {
    toggle.addEventListener('click', toggleSubmenu);
  });

  // NOVO: Event listener para todos os links do menu (exceto submenu toggles)
  sidebar.querySelectorAll('a[href]:not([href="#"]):not(.submenu-toggle)').forEach(link => {
    link.addEventListener('click', (e) => {
      // Expande sidebar se estiver colapsado (apenas desktop)
      if (window.innerWidth > 768) {
        expandSidebarOnItemClick();
      }
      
      // Se for mobile, fecha o sidebar
      if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
        setTimeout(closeMobileSidebar, 150);
      }
    });
  });

  // NOVO: Event listener especial para itens de submenu quando sidebar colapsado
  sidebar.addEventListener('click', (e) => {
    const clickedElement = e.target.closest('a');
    if (!clickedElement) return;

    const isSubmenuLink = clickedElement.classList.contains('submenu-link');
    const parentSubmenu = clickedElement.closest('.has-submenu');
    
    // Se clicou em um item de submenu e o sidebar está colapsado
    if (isSubmenuLink && parentSubmenu && sidebar.classList.contains('collapsed')) {
      // Expande o sidebar e abre o submenu
      sidebar.classList.remove('collapsed');
      setTimeout(() => {
        parentSubmenu.classList.add('open');
      }, 200);
    }
  });

  // NOVO: Comportamento especial para hover nos itens com submenu quando colapsado
  sidebar.addEventListener('mouseenter', (e) => {
    if (e.target.closest('.has-submenu') && sidebar.classList.contains('collapsed')) {
      const hasSubmenuItem = e.target.closest('.has-submenu');
      const tooltip = hasSubmenuItem.querySelector('.submenu-tooltip');
      if (tooltip) {
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
        tooltip.style.transform = 'translateX(0)';
      }
    }
  }, true);

  sidebar.addEventListener('mouseleave', (e) => {
    if (sidebar.classList.contains('collapsed')) {
      const tooltips = sidebar.querySelectorAll('.submenu-tooltip');
      tooltips.forEach(tooltip => {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
        tooltip.style.transform = 'translateX(-10px)';
      });
    }
  }, true);

  // NOVO: Redimensionamento da janela
  window.addEventListener('resize', () => {
    // Reconfigura tooltips quando a janela é redimensionada
    setTimeout(setupSubmenuTooltips, 100);
    
    // Remove estado mobile se mudou para desktop
    if (window.innerWidth > 768 && sidebar.classList.contains('open')) {
      closeMobileSidebar();
    }
  });

  console.log('Sidebar melhorado inicializado com sucesso');
});