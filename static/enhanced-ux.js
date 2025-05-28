
// ===== ENHANCED USER EXPERIENCE =====
class UXEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.setupKeyboardShortcuts();
        this.setupScrollEnhancements();
        this.setupFormEnhancements();
        this.setupSearchEnhancements();
        this.setupAccessibilityFeatures();
    }

    // Atalhos de teclado
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K para abrir busca
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.openQuickSearch();
            }

            // Ctrl/Cmd + , para abrir preferências
            if ((e.ctrlKey || e.metaKey) && e.key === ',') {
                e.preventDefault();
                if (typeof openPreferences === 'function') {
                    openPreferences();
                }
            }

            // Escape para fechar modais
            if (e.key === 'Escape') {
                this.closeAllModals();
            }

            // F1 para ajuda
            if (e.key === 'F1') {
                e.preventDefault();
                this.showHelp();
            }
        });
    }

    // Melhorias de scroll
    setupScrollEnhancements() {
        // Smooth scroll para links internos
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="#"]');
            if (link) {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });

        // Botão voltar ao topo
        this.createBackToTopButton();
    }

    // Criar botão voltar ao topo
    createBackToTopButton() {
        const button = document.createElement('button');
        button.className = 'back-to-top';
        button.innerHTML = '<i class="fas fa-chevron-up"></i>';
        button.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            opacity: 0;
            visibility: hidden;
            z-index: 1000;
        `;

        button.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // Verificar se document.body existe antes de adicionar
        if (document.body) {
            document.body.appendChild(button);
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                if (document.body) {
                    document.body.appendChild(button);
                }
            });
        }

        // Mostrar/esconder baseado no scroll
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                button.style.opacity = '1';
                button.style.visibility = 'visible';
            } else {
                button.style.opacity = '0';
                button.style.visibility = 'hidden';
            }
        });
    }

    // Melhorias de formulários
    setupFormEnhancements() {
        // Auto-save em formulários (verificar se cookieManager existe)
        if (typeof cookieManager !== 'undefined' && cookieManager.getPreference('autoSave')) {
            this.setupAutoSave();
        }

        // Validação em tempo real
        this.setupRealTimeValidation();
    }

    // Configurar melhorias de busca
    setupSearchEnhancements() {
        // Adicionar funcionalidade de busca em tempo real
        const searchInputs = document.querySelectorAll('input[type="search"], .search-input');
        searchInputs.forEach(input => {
            input.addEventListener('input', debounce((e) => {
                this.performSearch(e.target.value);
            }, 300));
        });

        // Destacar resultados de busca
        this.setupSearchHighlight();
    }

    // Realizar busca
    performSearch(query) {
        if (query.length < 2) return;
        
        // Implementar lógica de busca básica
        const searchableElements = document.querySelectorAll('[data-searchable], .searchable');
        searchableElements.forEach(element => {
            const text = element.textContent.toLowerCase();
            const matches = text.includes(query.toLowerCase());
            
            if (matches) {
                element.style.display = '';
                this.highlightText(element, query);
            } else {
                element.style.display = 'none';
            }
        });
    }

    // Destacar texto de busca
    highlightText(element, query) {
        if (!query) return;
        
        const regex = new RegExp(`(${query})`, 'gi');
        const originalHTML = element.dataset.originalHTML || element.innerHTML;
        
        if (!element.dataset.originalHTML) {
            element.dataset.originalHTML = originalHTML;
        }
        
        element.innerHTML = originalHTML.replace(regex, '<mark>$1</mark>');
    }

    // Configurar destaque de busca
    setupSearchHighlight() {
        // Limpar destaques ao clicar fora
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.clearSearchHighlights();
            }
        });
    }

    // Limpar destaques de busca
    clearSearchHighlights() {
        const highlightedElements = document.querySelectorAll('[data-original-html]');
        highlightedElements.forEach(element => {
            element.innerHTML = element.dataset.originalHTML;
            delete element.dataset.originalHTML;
        });
    }

    // Auto-save para formulários
    setupAutoSave() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                if (input.type !== 'password') {
                    const key = `autosave_${form.id || 'form'}_${input.name || input.id}`;
                    
                    // Carregar valor salvo (verificar se cookieManager existe)
                    if (typeof cookieManager !== 'undefined') {
                        const saved = cookieManager.getCookie(key);
                        if (saved) {
                            input.value = saved;
                        }

                        // Salvar em mudanças
                        input.addEventListener('input', debounce(() => {
                            cookieManager.setCookie(key, input.value, 1); // 1 dia
                        }, 500));
                    }
                }
            });
        });
    }

    // Validação em tempo real
    setupRealTimeValidation() {
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('input', () => {
                this.validateEmail(input);
            });
        });

        const passwordInputs = document.querySelectorAll('input[type="password"]');
        passwordInputs.forEach(input => {
            input.addEventListener('input', () => {
                this.validatePassword(input);
            });
        });
    }

    // Validar email
    validateEmail(input) {
        const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value);
        this.showFieldValidation(input, isValid, 'Email inválido');
    }

    // Validar senha
    validatePassword(input) {
        const isValid = input.value.length >= 8;
        this.showFieldValidation(input, isValid, 'Senha deve ter pelo menos 8 caracteres');
    }

    // Mostrar validação de campo
    showFieldValidation(input, isValid, errorMessage) {
        // Remover feedback anterior
        const existingFeedback = input.parentNode.querySelector('.field-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }

        // Adicionar classes
        input.classList.remove('field-valid', 'field-invalid');
        if (input.value) {
            input.classList.add(isValid ? 'field-valid' : 'field-invalid');

            // Adicionar feedback visual
            if (!isValid) {
                const feedback = document.createElement('span');
                feedback.className = 'field-feedback';
                feedback.textContent = errorMessage;
                feedback.style.cssText = `
                    color: var(--danger);
                    font-size: 0.8rem;
                    display: block;
                    margin-top: 4px;
                `;
                input.parentNode.appendChild(feedback);
            }
        }
    }

    // Busca rápida
    openQuickSearch() {
        // Implementar busca rápida
        if (typeof showToast === 'function') {
            showToast('Busca rápida: Ctrl+K', 'info');
        }
    }

    // Fechar todos os modais
    closeAllModals() {
        // Fechar modal de preferências
        if (window.preferencesManager && typeof window.preferencesManager.closeModal === 'function') {
            window.preferencesManager.closeModal();
        }

        // Fechar outros modais
        const modals = document.querySelectorAll('.modal, .preferences-modal');
        modals.forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.style.display = 'none';
            }
        });
    }

    // Mostrar ajuda
    showHelp() {
        const helpContent = `
            <h3>Atalhos de Teclado</h3>
            <p><strong>Ctrl+K:</strong> Busca rápida</p>
            <p><strong>Ctrl+,:</strong> Preferências</p>
            <p><strong>Escape:</strong> Fechar modais</p>
            <p><strong>F1:</strong> Esta ajuda</p>
        `;
        
        if (typeof showToast === 'function') {
            showToast(helpContent, 'info', 8000);
        }
    }

    // Melhorias de acessibilidade
    setupAccessibilityFeatures() {
        // Navegação por teclado
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });

        // Alto contraste (verificar se cookieManager existe)
        if (typeof cookieManager !== 'undefined' && cookieManager.getCookie('high_contrast') === 'true') {
            document.body.classList.add('high-contrast');
        }
    }
}

// Adicionar estilos de validação
function addValidationStyles() {
    const validationStyles = document.createElement('style');
    validationStyles.textContent = `
        .field-valid {
            border-color: var(--success) !important;
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2) !important;
        }
        
        .field-invalid {
            border-color: var(--danger) !important;
            box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2) !important;
        }
        
        .keyboard-navigation *:focus {
            outline: 2px solid var(--primary) !important;
            outline-offset: 2px;
        }
        
        .high-contrast {
            filter: contrast(150%);
        }

        mark {
            background-color: yellow;
            color: black;
            padding: 0 2px;
        }
    `;

    if (document.head) {
        document.head.appendChild(validationStyles);
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            if (document.head) {
                document.head.appendChild(validationStyles);
            }
        });
    }
}

// Utilitário debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Inicializar melhorias de UX quando DOM estiver pronto
function initializeUXEnhancer() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            addValidationStyles();
            window.uxEnhancer = new UXEnhancer();
        });
    } else {
        addValidationStyles();
        window.uxEnhancer = new UXEnhancer();
    }
}

initializeUXEnhancer();

console.log('✨ Melhorias de UX carregadas com sucesso');
