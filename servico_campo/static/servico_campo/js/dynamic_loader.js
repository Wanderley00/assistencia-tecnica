document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.getElementById('mainContent');
    const sidebar = document.getElementById('sidebar');

    if (!mainContent || !sidebar) {
        console.error("Estrutura principal (mainContent ou sidebar) não encontrada.");
        return;
    }

    // Array global para armazenar funções de inicialização de páginas
    window.initializePageScripts = [];

    // ===== CRIAÇÃO DOS ELEMENTOS DE LOADING =====
    
    // Criar overlay de loading
    const createLoadingOverlay = () => {
        const overlay = document.createElement('div');
        overlay.className = 'page-loading-overlay';
        overlay.id = 'pageLoadingOverlay';
        
        const container = document.createElement('div');
        container.className = 'loading-spinner-container';
        
        // Opção 1: Spinner tradicional
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        
        // Opção 2: Loading dots (comentado - descomente para usar)
        /*
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'loading-dots';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'loading-dot';
            dotsContainer.appendChild(dot);
        }
        */
        
        const text = document.createElement('div');
        text.className = 'loading-text';
        text.textContent = 'Carregando...';
        
        container.appendChild(spinner);
        // container.appendChild(dotsContainer); // Para usar dots em vez de spinner
        container.appendChild(text);
        overlay.appendChild(container);
        
        document.body.appendChild(overlay);
        return overlay;
    };

    // Criar barra de progresso
    const createProgressBar = () => {
        const progressBar = document.createElement('div');
        progressBar.className = 'page-progress-bar';
        progressBar.id = 'pageProgressBar';
        document.body.appendChild(progressBar);
        return progressBar;
    };

    // Inicializar elementos de loading
    const loadingOverlay = createLoadingOverlay();
    const progressBar = createProgressBar();

    // ===== FUNÇÕES DE CONTROLE DE LOADING =====

    const showLoading = () => {
        // Mostrar overlay
        loadingOverlay.classList.add('active');
        
        // Iniciar barra de progresso
        progressBar.style.width = '0%';
        progressBar.classList.add('active');
        
        // Simular progresso
        setTimeout(() => {
            progressBar.style.width = '30%';
        }, 100);
        
        // Adicionar classe loading ao conteúdo
        mainContent.classList.add('loading');
    };

    const updateProgress = (percentage) => {
        progressBar.style.width = percentage + '%';
    };

    const hideLoading = () => {
        // Completar barra de progresso
        progressBar.style.width = '100%';
        
        setTimeout(() => {
            // Esconder overlay
            loadingOverlay.classList.remove('active');
            
            // Esconder barra de progresso
            progressBar.classList.remove('active');
            setTimeout(() => {
                progressBar.style.width = '0%';
            }, 300);
            
            // Remover classe loading e adicionar fade-in
            mainContent.classList.remove('loading');
            mainContent.classList.add('fade-in');
            
            // Remover classe fade-in após animação
            setTimeout(() => {
                mainContent.classList.remove('fade-in');
            }, 500);
        }, 200);
    };

    // ===== FUNÇÕES ORIGINAIS MANTIDAS =====

    // Função aprimorada para encontrar e executar scripts de um container
    const executeScriptsInContainer = (container) => {
        if (!container) return;
        
        const scripts = container.querySelectorAll("script");
        scripts.forEach(script => {
            // Para scripts inline (sem atributo 'src')
            if (!script.src) {
                try {
                    // Executar o script no escopo global
                    window.eval(script.innerText);
                } catch (e) {
                    console.error("Erro ao executar script dinâmico:", e, script.innerText);
                }
            } else {
                // Para scripts externos (com atributo 'src'), criamos um novo script
                const newScript = document.createElement("script");
                // Copia todos os atributos, incluindo 'src' e 'type'
                for (const attr of script.attributes) {
                    newScript.setAttribute(attr.name, attr.value);
                }
                // Adiciona ao final do body para carregar e executar
                document.body.appendChild(newScript);
            }
        });
    };

    // Função para executar scripts de inicialização de páginas específicas
    const executePageInitScripts = () => {
        if (window.initializePageScripts && window.initializePageScripts.length > 0) {
            window.initializePageScripts.forEach(initFunction => {
                try {
                    if (typeof initFunction === 'function') {
                        initFunction();
                    }
                } catch (error) {
                    console.error('Erro ao executar função de inicialização:', error);
                }
            });
            // Limpar o array para evitar execuções duplicadas
            window.initializePageScripts = [];
        }
    };

    // Função para limpar recursos antigos antes de carregar novo conteúdo
    const cleanupResources = () => {
        // Limpar Chart.js instances se existirem
        if (window.Chart && window.Chart.instances) {
            window.Chart.instances.forEach(instance => {
                try {
                    instance.destroy();
                } catch (e) {
                    console.warn('Erro ao destruir instância Chart.js:', e);
                }
            });
        }

        // Limpar Google Charts se necessário
        if (window.google && window.google.visualization) {
            // Limpar qualquer gráfico existente
            const chartDivs = document.querySelectorAll('[id*="chart"], [id*="Chart"]');
            chartDivs.forEach(div => {
                if (div.innerHTML) {
                    div.innerHTML = '';
                }
            });
        }

        // Resetar variáveis globais do gráfico Gantt se existirem
        if (window.timelineChart) {
            try {
                window.timelineChart.clearChart();
            } catch (e) {
                // Ignore se não conseguir limpar
            }
            window.timelineChart = null;
        }
        if (window.isGoogleChartsLoaded !== undefined) {
            window.isGoogleChartsLoaded = false;
        }
        if (window.chartInitialized !== undefined) {
            window.chartInitialized = false;
        }

        // Limpar event listeners antigos clonando elementos
        const oldButtons = document.querySelectorAll('#apply_filter_btn, #reset_filter_btn');
        oldButtons.forEach(btn => {
            const newBtn = btn.cloneNode(true);
            if (btn.parentNode) {
                btn.parentNode.replaceChild(newBtn, btn);
            }
        });

        // Limpar timeouts e intervals se existirem
        if (window.chartTimeout) {
            clearTimeout(window.chartTimeout);
            window.chartTimeout = null;
        }
    };

    // ===== FUNÇÃO MELHORADA DE ATUALIZAÇÃO DO MENU ATIVO =====
    
    const normalizeUrl = (url) => {
        try {
            // Remove parâmetros de query e fragmentos
            const urlObj = new URL(url, window.location.origin);
            let pathname = urlObj.pathname;
            
            // Remove trailing slash, exceto para root
            if (pathname !== '/' && pathname.endsWith('/')) {
                pathname = pathname.slice(0, -1);
            }
            
            return pathname;
        } catch (e) {
            console.warn('Erro ao normalizar URL:', url, e);
            return url;
        }
    };

    const updateActiveMenuItem = (currentUrl) => {
        console.log('🔄 Atualizando menu ativo para URL:', currentUrl);
        
        // Normalizar a URL atual
        const normalizedCurrentUrl = normalizeUrl(currentUrl);
        console.log('📍 URL normalizada:', normalizedCurrentUrl);
        
        // Remove classe active de todos os links
        sidebar.querySelectorAll('.menu-link, .submenu-link').forEach(link => {
            link.classList.remove('active');
            const parent = link.closest('.menu-item');
            if (parent) {
                parent.classList.remove('active');
            }
        });

        // Remove classe open de todos os submenus
        sidebar.querySelectorAll('.has-submenu').forEach(submenu => {
            submenu.classList.remove('open');
        });

        // Encontra e ativa o link correspondente
        let activeLink = null;
        const allLinks = sidebar.querySelectorAll('a[href]');
        
        // Primeiro, tenta encontrar uma correspondência exata
        allLinks.forEach(link => {
            const linkHref = link.getAttribute('href');
            if (linkHref && linkHref !== '#') {
                const normalizedLinkUrl = normalizeUrl(linkHref);
                console.log('🔗 Comparando:', normalizedLinkUrl, 'com', normalizedCurrentUrl);
                
                if (normalizedLinkUrl === normalizedCurrentUrl) {
                    activeLink = link;
                    console.log('✅ Link ativo encontrado:', link);
                }
            }
        });

        // Se não encontrou correspondência exata, tenta correspondência parcial para subpáginas
        if (!activeLink) {
            allLinks.forEach(link => {
                const linkHref = link.getAttribute('href');
                if (linkHref && linkHref !== '#') {
                    const normalizedLinkUrl = normalizeUrl(linkHref);
                    
                    // Verifica se a URL atual começa com a URL do link (para subpáginas)
                    if (normalizedCurrentUrl.startsWith(normalizedLinkUrl) && normalizedLinkUrl !== '/') {
                        activeLink = link;
                        console.log('✅ Link ativo encontrado (correspondência parcial):', link);
                    }
                }
            });
        }

        // Fallback para página inicial
        if (!activeLink && (normalizedCurrentUrl === '/' || normalizedCurrentUrl === '')) {
            const dashboardLink = sidebar.querySelector('a[href*="dashboard"]');
            if (dashboardLink) {
                activeLink = dashboardLink;
                console.log('✅ Ativando Dashboard como fallback para página inicial');
            }
        }

        if (activeLink) {
            // Adicionar classe active ao link
            activeLink.classList.add('active');
            console.log('🎯 Classe active adicionada ao link');
            
            // Adicionar classe active ao item pai
            const parentMenuItem = activeLink.closest('.menu-item');
            if (parentMenuItem) {
                parentMenuItem.classList.add('active');
                console.log('📁 Classe active adicionada ao item pai');
            }
            
            // Se estiver em um submenu, abrir o submenu pai
            const submenu = activeLink.closest('.submenu');
            if (submenu) {
                const parentItem = submenu.closest('.has-submenu');
                if (parentItem) {
                    parentItem.classList.add('open');
                    console.log('📂 Submenu pai aberto');
                    
                    // Se o sidebar estiver colapsado, expandi-lo automaticamente
                    if (sidebar.classList.contains('collapsed')) {
                        sidebar.classList.remove('collapsed');
                        console.log('📖 Sidebar expandido automaticamente');
                    }
                }
            }
            
            // Adicionar atributo data-tooltip para todos os links do menu
            const menuText = activeLink.querySelector('.menu-text, .submenu-text');
            if (menuText) {
                activeLink.setAttribute('data-tooltip', menuText.textContent.trim());
            }
            
            // Adicionar efeito visual temporário
            activeLink.style.transform = 'scale(1.02)';
            setTimeout(() => {
                activeLink.style.transform = '';
            }, 200);
            
        } else {
            console.warn('⚠️ Nenhum link ativo encontrado para URL:', normalizedCurrentUrl);
        }
    };

    // ===== FUNÇÃO PRINCIPAL DE CARREGAMENTO COM LOADING =====

    const loadContent = async (url, isPopState = false) => {
        try {
            // Previne múltiplos carregamentos simultâneos
            if (mainContent.dataset.loading === 'true') {
                return;
            }
            mainContent.dataset.loading = 'true';

            // Mostrar loading
            showLoading();

            // Simular progresso inicial
            updateProgress(10);

            // Limpar recursos antes de carregar novo conteúdo
            cleanupResources();
            updateProgress(20);

            const response = await fetch(url, {
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html'
                },
                credentials: 'same-origin'
            });

            updateProgress(50);

            if (!response.ok) {
                throw new Error(`Erro ${response.status}: ${response.statusText}`);
            }

            const html = await response.text();
            updateProgress(70);

            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const newContent = doc.querySelector('.page-content');
            const newExtraJs = doc.getElementById('extra-js-container');
            const newTitle = doc.querySelector('title')?.innerText || document.title;
            
            if (!newContent) {
                throw new Error('Conteúdo .page-content não encontrado na resposta');
            }

            updateProgress(80);

            // Atualizar conteúdo
            document.title = newTitle;
            const pageContent = document.querySelector('.page-content');
            if (pageContent) {
                pageContent.innerHTML = newContent.innerHTML;
            }
            
            const jsContainer = document.getElementById('extra-js-container');
            if (jsContainer) {
                jsContainer.innerHTML = newExtraJs ? newExtraJs.innerHTML : '';
            }

            updateProgress(90);

            // Atualizar estado ativo do menu APÓS o conteúdo ser carregado
            setTimeout(() => {
                updateActiveMenuItem(url);
            }, 100);

            // Executar scripts do novo conteúdo
            executeScriptsInContainer(jsContainer);
            executeScriptsInContainer(document.querySelector('.page-content'));

            updateProgress(95);

            // Aguardar um breve momento para garantir que o DOM seja atualizado
            setTimeout(() => {
                executePageInitScripts();
                updateProgress(100);
                
                // Esconder loading após pequeno delay
                setTimeout(() => {
                    hideLoading();
                }, 100);
            }, 100);

            // Atualizar histórico do navegador
            if (!isPopState) {
                history.pushState({ path: url }, '', url);
            }

            console.log(`✅ Conteúdo carregado dinamicamente: ${url}`);

        } catch (error) {
            console.error('❌ Erro ao carregar conteúdo:', error);
            
            // Esconder loading em caso de erro
            hideLoading();
            
            // Em caso de erro, fazer fallback para carregamento normal
            // mas apenas se não for um erro de rede temporário
            if (!error.message.includes('Failed to fetch')) {
                window.location.href = url;
            } else {
                // Para erros de rede, mostrar mensagem e manter na página atual
                const pageContent = document.querySelector('.page-content');
                if (pageContent) {
                    pageContent.innerHTML = `
                        <div class="alert alert-danger mt-4">
                            <h5>Erro de Conexão</h5>
                            <p>Não foi possível carregar a página. Verifique sua conexão e tente novamente.</p>
                            <button class="btn btn-primary" onclick="location.reload()">Recarregar Página</button>
                        </div>
                    `;
                }
            }
        } finally {
            // Limpar flag de loading
            mainContent.dataset.loading = 'false';
        }
    };

    // ===== EVENT LISTENERS =====

    // Event listener melhorado para cliques na sidebar
    sidebar.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (!link || !link.href) {
            return;
        }

        // Verificar se é um link válido para carregamento dinâmico
        const url = new URL(link.href);
        const currentUrl = new URL(window.location.href);
        
        // Só processar se for do mesmo domínio e não for logout
        if (url.hostname !== currentUrl.hostname || 
            link.href.includes('/logout/') ||
            link.href.includes('javascript:') ||
            link.href.startsWith('mailto:') ||
            link.href.startsWith('tel:')) {
            return;
        }

        // Se for um toggle de submenu, deixar o sidebar.js lidar com isso
        if (link.classList.contains('submenu-toggle') || link.getAttribute('href') === '#') {
            return;
        }

        // Se for um link de submenu e o sidebar estiver colapsado,
        // deixar o sidebar.js expandir primeiro
        const isSubmenuLink = link.classList.contains('submenu-link');
        const parentSubmenu = link.closest('.has-submenu');
        
        if (isSubmenuLink && parentSubmenu && sidebar.classList.contains('collapsed')) {
            setTimeout(() => {
                e.preventDefault();
                loadContent(link.href);
            }, 300);
            return;
        }

        // Para links normais, carregar conteúdo dinamicamente
        e.preventDefault();
        loadContent(link.href);
    });

    // Event listener para navegação do browser (botões voltar/avançar)
    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.path) {
            loadContent(e.state.path, true);
        } else {
            loadContent(window.location.href, true);
        }
    });

    // ===== INICIALIZAÇÃO =====

    // Adicionar estado inicial ao histórico
    if (!history.state) {
        history.replaceState({ path: window.location.href }, '', window.location.href);
    }

    // Atualizar menu ativo na carga inicial com delay para garantir que o DOM esteja pronto
    setTimeout(() => {
        updateActiveMenuItem(window.location.href);
        console.log('🚀 Menu ativo inicializado');
    }, 100);

    // Adicionar tooltips para todos os links do menu
    sidebar.querySelectorAll('.menu-link').forEach(link => {
        const menuText = link.querySelector('.menu-text');
        if (menuText) {
            link.setAttribute('data-tooltip', menuText.textContent.trim());
        }
    });

    // Executar scripts de inicialização para a página atual
    setTimeout(() => {
        executePageInitScripts();
    }, 200);

    console.log('🎉 Dynamic Loader melhorado inicializado com sucesso');
});
