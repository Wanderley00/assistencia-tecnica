document.addEventListener("DOMContentLoaded", function() {
    const body = document.querySelector('body'),
          sidebar = body.querySelector('.sidebar'),
          toggle = body.querySelector(".toggle");

    // Função para detectar se é dispositivo móvel
    function isMobile() {
        return window.innerWidth <= 768;
    }

    // Criar overlay para mobile
    function createOverlay() {
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
            
            // Fechar menu ao clicar no overlay
            overlay.addEventListener('click', function() {
                closeMobileMenu();
            });
        }
        return overlay;
    }

    // Criar botão toggle para mobile (3 barras)
    function createMobileToggle() {
        let mobileToggle = document.querySelector('.mobile-menu-toggle');
        if (!mobileToggle) {
            mobileToggle = document.createElement('button');
            mobileToggle.className = 'mobile-menu-toggle';
            mobileToggle.innerHTML = '<i class="bi bi-list"></i>';
            document.body.appendChild(mobileToggle);
            
            // Abrir menu ao clicar no botão mobile
            mobileToggle.addEventListener('click', function() {
                openMobileMenu();
            });
        }
        return mobileToggle;
    }

    // Abrir menu mobile
    function openMobileMenu() {
        const overlay = createOverlay();
        const mobileToggle = document.querySelector('.mobile-menu-toggle');
        
        sidebar.classList.add('active');
        overlay.classList.add('active');
        
        // Ocultar botão de 3 barras quando menu estiver aberto
        if (mobileToggle) {
            mobileToggle.style.display = 'none';
        }
        
        // Adicionar listener para o botão X (pseudo-elemento)
        addCloseButtonListener();
    }

    // Fechar menu mobile
    function closeMobileMenu() {
        const overlay = document.querySelector('.sidebar-overlay');
        const mobileToggle = document.querySelector('.mobile-menu-toggle');
        
        sidebar.classList.remove('active');
        
        if (overlay) {
            overlay.classList.remove('active');
        }
        
        // Mostrar botão de 3 barras novamente quando menu fechar
        if (mobileToggle) {
            mobileToggle.style.display = 'block';
        }
        
        // Remover listener do botão X
        removeCloseButtonListener();
    }

    // Adicionar listener para o botão X (criamos um elemento invisível sobre o pseudo-elemento)
    function addCloseButtonListener() {
        // Remove listener anterior se existir
        removeCloseButtonListener();
        
        // Criar elemento invisível para capturar cliques no X
        const closeButton = document.createElement('div');
        closeButton.className = 'mobile-close-button';
        closeButton.style.cssText = `
            position: absolute;
            top: 15px;
            right: 15px;
            width: 35px;
            height: 35px;
            z-index: 1053;
            cursor: pointer;
        `;
        
        closeButton.addEventListener('click', closeMobileMenu);
        sidebar.appendChild(closeButton);
    }

    // Remover listener do botão X
    function removeCloseButtonListener() {
        const existingCloseButton = sidebar.querySelector('.mobile-close-button');
        if (existingCloseButton) {
            existingCloseButton.remove();
        }
    }

    // Configurar comportamento baseado no tamanho da tela
    function setupResponsiveBehavior() {
        if (isMobile()) {
            // Modo mobile: criar elementos necessários
            createOverlay();
            const mobileToggle = createMobileToggle();
            
            // Remover a classe 'close' se existir (não é usada em mobile)
            sidebar.classList.remove('close');
            
            // OCULTAR o toggle original (seta) em mobile
            if (toggle) {
                toggle.style.display = 'none';
            }
            
            // Mostrar botão de 3 barras se o menu não estiver ativo
            if (mobileToggle && !sidebar.classList.contains('active')) {
                mobileToggle.style.display = 'block';
            }
            
            // Configurar o toggle original para fechar o menu em mobile (caso seja clicado)
            if (toggle) {
                toggle.onclick = function() {
                    closeMobileMenu();
                };
            }
        } else {
            // Modo desktop: comportamento original
            sidebar.classList.remove('active');
            
            // MOSTRAR o toggle original (seta) em desktop
            if (toggle) {
                toggle.style.display = 'flex';
            }
            
            // Remover overlay e botão mobile se existirem
            const overlay = document.querySelector('.sidebar-overlay');
            const mobileToggle = document.querySelector('.mobile-menu-toggle');
            
            if (overlay) {
                overlay.classList.remove('active');
            }
            if (mobileToggle) {
                mobileToggle.style.display = 'none';
            }
            
            // Restaurar comportamento original do toggle
            if (toggle) {
                toggle.onclick = function() {
                    sidebar.classList.toggle("close");
                };
            }
        }
    }

    // Configuração inicial
    setupResponsiveBehavior();

    // Reconfigurar quando a janela é redimensionada
    window.addEventListener('resize', function() {
        setupResponsiveBehavior();
        
        // Se mudou de mobile para desktop com menu aberto, fechar
        if (!isMobile() && sidebar.classList.contains('active')) {
            closeMobileMenu();
        }
    });

    // Fechar menu mobile ao pressionar ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && isMobile() && sidebar.classList.contains('active')) {
            closeMobileMenu();
        }
    });

    // Prevenção de scroll do body quando o menu está aberto em mobile
    function preventBodyScroll(prevent) {
        if (prevent) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }

    // Observer para mudanças na classe 'active' do sidebar em mobile
    if (sidebar) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    if (isMobile()) {
                        const isActive = sidebar.classList.contains('active');
                        preventBodyScroll(isActive);
                    }
                }
            });
        });

        observer.observe(sidebar, {
            attributes: true,
            attributeFilter: ['class']
        });
    }
});