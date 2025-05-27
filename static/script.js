// ===== GLOBAL VARIABLES =====
let toastContainer;
let navToggle;
let navMenu;

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupNavigation();
    setupToastContainer();
    checkAuthenticationStatus();
    setupGlobalEventListeners();
});

// ===== APP INITIALIZATION =====
function initializeApp() {
    console.log('FovDark System Initialized');

    // Add loading animations to cards
    animateElements();

    // Setup auth state
    updateAuthenticationUI();
}

// ===== NAVIGATION =====
function setupNavigation() {
    navToggle = document.getElementById('navToggle');
    navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', toggleMobileMenu);
    }

    // Close mobile menu when clicking on links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', closeMobileMenu);
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (navMenu && navMenu.classList.contains('active') && 
            !navMenu.contains(e.target) && !navToggle.contains(e.target)) {
            closeMobileMenu();
        }
    });
}

function toggleMobileMenu() {
    if (navMenu) {
        navMenu.classList.toggle('active');
        navToggle.classList.toggle('active');

        // Animate hamburger bars
        const bars = navToggle.querySelectorAll('.bar');
        bars.forEach((bar, index) => {
            if (navToggle.classList.contains('active')) {
                if (index === 0) bar.style.transform = 'rotate(45deg) translate(5px, 5px)';
                if (index === 1) bar.style.opacity = '0';
                if (index === 2) bar.style.transform = 'rotate(-45deg) translate(7px, -6px)';
            } else {
                bar.style.transform = '';
                bar.style.opacity = '1';
            }
        });
    }
}

function closeMobileMenu() {
    if (navMenu && navToggle) {
        navMenu.classList.remove('active');
        navToggle.classList.remove('active');

        // Reset hamburger bars
        const bars = navToggle.querySelectorAll('.bar');
        bars.forEach(bar => {
            bar.style.transform = '';
            bar.style.opacity = '1';
        });
    }
}

// ===== AUTHENTICATION =====
function checkAuthenticationStatus() {
    const token = localStorage.getItem('access_token');
    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');

    if (token && userData) {
        // Verificar se o token ainda é válido
        fetch('/api/license/check', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }).then(response => {
            if (response.status === 401) {
                // Token expirado
                logout();
            }
        }).catch(error => {
            console.log('Erro ao verificar token:', error);
        });
    }

    updateAuthenticationUI();
}

function updateAuthenticationUI() {
    const token = localStorage.getItem('access_token');
    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');

    const loginLink = document.getElementById('loginLink');
    const logoutLink = document.getElementById('logoutLink');
    const painelLink = document.getElementById('painelLink');
    const adminLink = document.getElementById('adminLink');

    if (token && userData.email) {
        // Usuário logado
        if (loginLink) loginLink.style.display = 'none';
        if (logoutLink) logoutLink.style.display = 'flex';
        if (painelLink) painelLink.style.display = 'flex';

        // Mostrar link admin apenas para administradores
        if (adminLink) {
            adminLink.style.display = userData.is_admin ? 'flex' : 'none';
        }
    } else {
        // Usuário não logado
        if (loginLink) loginLink.style.display = 'flex';
        if (logoutLink) logoutLink.style.display = 'none';
        if (painelLink) painelLink.style.display = 'none';
        if (adminLink) adminLink.style.display = 'none';
    }
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');

    showToast('Logout realizado com sucesso', 'success');

    // Redirecionar para home após 1 segundo
    setTimeout(() => {
        window.location.href = '/';
    }, 1000);
}

// ===== TOAST NOTIFICATIONS =====
function setupToastContainer() {
    toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
}

function showToast(message, type = 'info', duration = 5000) {
    if (!toastContainer) {
        setupToastContainer();
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };

    toast.innerHTML = `
        <i class="toast-icon ${icons[type] || icons.info}"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="removeToast(this.parentElement)">
            <i class="fas fa-times"></i>
        </button>
    `;

    toastContainer.appendChild(toast);

    // Auto remove after duration
    setTimeout(() => {
        removeToast(toast);
    }, duration);

    // Add click to close
    toast.addEventListener('click', function(e) {
        if (e.target.classList.contains('toast-close') || e.target.parentElement.classList.contains('toast-close')) {
            removeToast(toast);
        }
    });
}

function removeToast(toast) {
    if (toast && toast.parentElement) {
        toast.style.animation = 'toastSlideOut 0.3s ease forwards';
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }
}

// ===== FORM UTILITIES =====
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('pt-BR');
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('pt-BR');
}

// ===== ANIMATIONS =====
function animateElements() {
    // Observe elements for scroll animations
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-slide-up');
                }
            });
        },
        { threshold: 0.1 }
    );

    // Observe cards and sections
    document.querySelectorAll('.feature-card, .pricing-card, .dashboard-card').forEach(el => {
        observer.observe(el);
    });
}

function addLoadingSpinner(element, text = 'Carregando...') {
    if (!element) return;

    const originalContent = element.innerHTML;
    element.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        ${text}
    `;
    element.disabled = true;

    return () => {
        element.innerHTML = originalContent;
        element.disabled = false;
    };
}

// ===== API UTILITIES =====
async function makeAuthenticatedRequest(url, options = {}) {
    const token = localStorage.getItem('access_token');

    if (!token) {
        throw new Error('Usuário não autenticado');
    }

    const headers = {
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Token expirado
        logout();
        throw new Error('Sessão expirada');
    }

    return response;
}

// ===== UTILITY FUNCTIONS =====
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

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text).then(() => {
            showToast('Copiado para a área de transferência', 'success');
        });
    } else {
        // Fallback para navegadores mais antigos
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            showToast('Copiado para a área de transferência', 'success');
        } catch (err) {
            showToast('Erro ao copiar', 'error');
        } finally {
            textArea.remove();
        }
    }
}

function generateRandomId() {
    return Math.random().toString(36).substr(2, 9);
}

function sanitizeInput(input) {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
}

// ===== SCROLL UTILITIES =====
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

function getScrollPercentage() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    return (scrollTop / scrollHeight) * 100;
}

// ===== LOCAL STORAGE UTILITIES =====
function setLocalStorageItem(key, value, expirationMinutes = null) {
    const item = {
        value: value,
        timestamp: Date.now()
    };

    if (expirationMinutes) {
        item.expiration = Date.now() + (expirationMinutes * 60 * 1000);
    }

    localStorage.setItem(key, JSON.stringify(item));
}

function getLocalStorageItem(key) {
    const itemStr = localStorage.getItem(key);

    if (!itemStr) {
        return null;
    }

    try {
        const item = JSON.parse(itemStr);

        // Verificar expiração
        if (item.expiration && Date.now() > item.expiration) {
            localStorage.removeItem(key);
            return null;
        }

        return item.value;
    } catch (e) {
        // Se não conseguir fazer parse, assumir que é um valor simples
        return itemStr;
    }
}

// ===== PERFORMANCE MONITORING =====
function measurePerformance(name, fn) {
    return function(...args) {
        const start = performance.now();
        const result = fn.apply(this, args);
        const end = performance.now();

        console.log(`${name} executado em ${end - start} millisegundos`);

        return result;
    };
}

// ===== DEVICE DETECTION =====
function isMobile() {
    return window.innerWidth <= 768;
}

function isTablet() {
    return window.innerWidth > 768 && window.innerWidth <= 1024;
}

function isDesktop() {
    return window.innerWidth > 1024;
}

// ===== KEYBOARD SHORTCUTS =====
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K para abrir busca
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            // Implementar busca se necessário
            console.log('Busca ativada');
        }

        // ESC para fechar modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                if (modal.style.display === 'flex') {
                    modal.style.display = 'none';
                }
            });
        }
    });
}

// ===== ERROR HANDLING =====
function handleGlobalErrors() {
    window.addEventListener('error', function(e) {
        console.error('Erro global capturado:', e.error);
        showToast('Ocorreu um erro inesperado', 'error');
    });

    window.addEventListener('unhandledrejection', function(e) {
        console.error('Promise rejeitada:', e.reason);
        showToast('Erro de conexão', 'error');
    });
}

// ===== THEME UTILITIES =====
function getPreferredTheme() {
    return localStorage.getItem('theme') || 
           (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
}

function setTheme(theme) {
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
}

// ===== CONNECTION STATUS =====
function monitorConnection() {
    function updateConnectionStatus() {
        if (navigator.onLine) {
            showToast('Conexão restaurada', 'success', 3000);
        } else {
            showToast('Conexão perdida', 'warning', 5000);
        }
    }

    window.addEventListener('online', updateConnectionStatus);
    window.addEventListener('offline', updateConnectionStatus);
}

// ===== GLOBAL EVENT LISTENERS =====
function setupGlobalEventListeners() {
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();

    // Setup error handling
    handleGlobalErrors();

    // Monitor connection
    monitorConnection();

    // Update auth UI on storage changes
    window.addEventListener('storage', function(e) {
        if (e.key === 'access_token' || e.key === 'user_data') {
            updateAuthenticationUI();
        }
    });

    // Smooth scroll for anchor links
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[href^="#"]');
        if (link) {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            smoothScrollTo(targetId);
        }
    });

    // Auto-resize textareas
    document.addEventListener('input', function(e) {
        if (e.target.tagName === 'TEXTAREA') {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
        }
    });
}

// ===== FEATURE DETECTION =====
function checkFeatureSupport() {
    const features = {
        localStorage: typeof(Storage) !== "undefined",
        fetch: typeof(fetch) !== "undefined",
        webGL: !!window.WebGLRenderingContext,
        webWorkers: typeof(Worker) !== "undefined",
        geolocation: 'geolocation' in navigator,
        notifications: 'Notification' in window
    };

    console.log('Recursos suportados:', features);
    return features;
}

// Função para abrir links externos
function openExternalLink(url, platform) {
    window.open(url, '_blank');

    // Log da ação
    console.log(`Link externo aberto: ${platform} - ${url}`);

    // Opcional: Rastrear cliques
    if (typeof gtag !== 'undefined') {
        gtag('event', 'external_link_click', {
            'platform': platform,
            'url': url
        });
    }
}

// Verificar se o site tem SSL
function checkSSL() {
    if (location.protocol === 'https:') {
        console.log('✓ Conexão SSL Segura');
        return true;
    } else {
        console.warn('⚠ Conexão não segura');
        return false;
    }
}

// Inicializar verificações de segurança
document.addEventListener('DOMContentLoaded', function() {
    checkSSL();

    // Adicionar indicador SSL ao footer se existir
    const footer = document.querySelector('.footer');
    if (footer && location.protocol === 'https:') {
        const sslBadge = document.createElement('div');
        sslBadge.className = 'ssl-badge';
        sslBadge.innerHTML = '<i class="fas fa-lock"></i> Conexão Segura SSL';
        sslBadge.style.cssText = 'color: #00ff8c; font-size: 0.8rem; margin-top: 1rem; text-align: center;';
        footer.appendChild(sslBadge);
    }
});

// Função para processar pagamento
async function processPayment(plano) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showToast('Você precisa estar logado para comprar', 'error');
        window.location.href = '/login';
        return;
    }

    try {
        const response = await fetch('/api/mercadopago/create-preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ plan_id: plano })
        });

        const data = await response.json();

        if (response.ok) {
            // Redirecionar para o Mercado Pago
            const initPoint = data.init_point || data.sandbox_init_point;
            if (initPoint) {
                window.location.href = initPoint;
            } else {
                showToast('Erro ao gerar link de pagamento', 'error');
            }
        } else {
            showToast(data.detail || 'Erro ao processar pagamento', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro de conexão', 'error');
    }
}

function toggleFaq(element) {
    const faqItem = element.parentElement;
    const answer = faqItem.querySelector('.faq-answer');
    const icon = element.querySelector('i');

    // Fechar outros FAQs
    document.querySelectorAll('.faq-item').forEach(item => {
        if (item !== faqItem && item.classList.contains('active')) {
            item.classList.remove('active');
            const otherAnswer = item.querySelector('.faq-answer');
            const otherIcon = item.querySelector('.faq-question i');
            otherAnswer.style.maxHeight = '0';
            if (otherIcon) {
                otherIcon.style.transform = 'rotate(0deg)';
            }
        }
    });

    // Toggle atual
    const isActive = faqItem.classList.contains('active');

    if (isActive) {
        // Fechar
        faqItem.classList.remove('active');
        answer.style.maxHeight = '0';
        if (icon) {
            icon.style.transform = 'rotate(0deg)';
        }
    } else {
        // Abrir
        faqItem.classList.add('active');

        // Calcular altura necessária
        const scrollHeight = answer.scrollHeight;
        answer.style.maxHeight = scrollHeight + 'px';

        if (icon) {
            icon.style.transform = 'rotate(180deg)';
        }

        // Adicionar efeito de bounce sutil
        setTimeout(() => {
            answer.style.maxHeight = (scrollHeight + 10) + 'px';
            setTimeout(() => {
                answer.style.maxHeight = scrollHeight + 'px';
            }, 100);
        }, 200);

        // Scroll suave para o item se necessário
        setTimeout(() => {
            const rect = faqItem.getBoundingClientRect();
            const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight;

            if (!isVisible) {
                faqItem.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest'
                });
            }
        }, 300);
    }
}

// Função para carregar produtos da API
async function loadProducts() {
    try {
        console.log('Carregando produtos...');
        const response = await fetch('/api/products');

        if (response.ok) {
            const products = await response.json();
            console.log('Produtos carregados:', products);
            displayProducts(products);
        } else {
            console.error('Erro ao carregar produtos:', response.status);
            showToast('Erro ao carregar produtos', 'error');
        }
    } catch (error) {
        console.error('Erro de conexão:', error);
        showToast('Erro de conexão ao carregar produtos', 'error');
    }
}

// Função para exibir produtos na página
function displayProducts(products) {
    const container = document.querySelector('.pricing-grid');
    if (!container) {
        console.warn('Container de produtos não encontrado');
        return;
    }

    if (products.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-secondary);">
                <i class="fas fa-box-open" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <h3>Nenhum produto disponível</h3>
                <p>Novos produtos serão adicionados em breve.</p>
            </div>
        `;
        return;
    }

    // Limpar container
    container.innerHTML = '';

    // Adicionar produtos
    products.forEach(product => {
        const productCard = createProductCard(product);
        container.appendChild(productCard);
    });
}

// Função para criar card de produto
function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'pricing-plan';

    const features = product.features ? product.features.split(',') : [];
    const featuresHTML = features.map(feature => `<li><i class="fas fa-check"></i>${feature.trim()}</li>`).join('');

    card.innerHTML = `
        ${product.is_featured ? '<div class="plan-badge">RECOMENDADO</div>' : ''}
        <div class="plan-header">
            <h3 class="plan-name">${product.name}</h3>
            <div class="plan-price">
                <span class="currency">R$</span>
                <span class="amount">${product.price.toFixed(2)}</span>
                <span class="period">/${product.duration_days} dias</span>
            </div>
        </div>

        <div class="plan-description">
            <p>${product.description || 'Acesso completo às funcionalidades premium'}</p>
        </div>

        <ul class="plan-features">
            ${featuresHTML || `
                <li><i class="fas fa-check"></i>Aim Assist Avançado</li>
                <li><i class="fas fa-check"></i>ESP & Wallhack</li>
                <li><i class="fas fa-check"></i>Anti-Detection</li>
                <li><i class="fas fa-check"></i>Suporte 24/7</li>
            `}
        </ul>

        <button class="plan-button" onclick="selectPlan('${product.id}', ${product.price}, '${product.name}', ${product.duration_days})">
            ESCOLHER PLANO
        </button>
    `;

    return card;
}

function selectPlan(productId, price, planName, durationDays) {
    selectedPlanData = { 
        id: productId, 
        type: productId, 
        price: price, 
        name: planName,
        duration: durationDays
    };

    // Verificar se usuário está logado
    const token = localStorage.getItem('access_token');
    if (!token) {
        // Mostrar prompt de login
        document.getElementById('loginPrompt').style.display = 'block';
        document.getElementById('checkoutForm').style.display = 'none';
    } else {
        // Mostrar formulário de checkout
        document.getElementById('loginPrompt').style.display = 'none';
        document.getElementById('checkoutForm').style.display = 'block';

        // Atualizar informações do plano
        document.getElementById('selectedPlanName').textContent = planName;
        document.getElementById('selectedPlanPrice').textContent = `R$ ${price.toFixed(2)}`;
    }

    // Abrir modal
    document.getElementById('checkoutModal').style.display = 'flex';
}

// Função de login melhorada
async function loginUser(email, password) {
    try {
        console.log('Tentando fazer login para:', email);
        
        const formData = new FormData();
        formData.append('email', email);
        formData.append('password', password);

        const response = await fetch('/api/login', {
            method: 'POST',
            body: formData
        });

        console.log('Resposta do servidor:', response.status);

        if (!response.ok) {
            let errorMessage = 'Erro no login';
            
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                console.error('Erro ao parsear resposta de erro:', e);
                if (response.status === 401) {
                    errorMessage = 'Email ou senha incorretos';
                } else if (response.status === 500) {
                    errorMessage = 'Erro interno do servidor';
                } else {
                    errorMessage = `Erro ${response.status}: ${response.statusText}`;
                }
            }
            
            showToast(errorMessage, 'error');
            throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('Login bem-sucedido:', data);

        if (data.access_token && data.user) {
            // Salvar dados do usuário
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_data', JSON.stringify(data.user));

            showToast('Login realizado com sucesso!', 'success');
            updateAuthenticationUI();
            
            return data;
        } else {
            throw new Error('Dados de resposta inválidos');
        }
        
    } catch (error) {
        console.error('Erro no login:', error);
        showToast(error.message || 'Erro inesperado no login', 'error');
        throw error;
    }
}

// Função de login principal
async function login(event) {
    if (event) {
        event.preventDefault();
    }

    const emailField = document.getElementById('email');
    const passwordField = document.getElementById('password');
    
    if (!emailField || !passwordField) {
        showToast('Campos de login não encontrados', 'error');
        return;
    }

    const email = emailField.value.trim();
    const password = passwordField.value;

    if (!email || !password) {
        showToast('Preencha todos os campos', 'error');
        return;
    }

    // Validar email
    if (!validateEmail(email)) {
        showToast('Email inválido', 'error');
        return;
    }

    // Mostrar loading
    const submitBtn = document.querySelector('button[type="submit"]') || document.getElementById('login-btn');
    if (!submitBtn) {
        showToast('Botão de login não encontrado', 'error');
        return;
    }

    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> CONECTANDO...';
    submitBtn.disabled = true;

    try {
        const loginData = await loginUser(email, password);
        
        // Verificar se há redirecionamento específico
        const urlParams = new URLSearchParams(window.location.search);
        const redirect = urlParams.get('redirect');

        setTimeout(() => {
            if (redirect === 'comprar') {
                window.location.href = '/comprar?from=login';
            } else if (loginData.user && loginData.user.is_admin) {
                window.location.href = '/admin';
            } else {
                window.location.href = '/painel';
            }
        }, 1000);

    } catch (error) {
        // Erro já foi tratado na função loginUser
    } finally {
        // Restaurar botão
        if (submitBtn) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
}

// ===== INITIALIZATION COMPLETE =====
console.log('FovDark Script carregado com sucesso');

// ===== EXPORT FOR TESTING =====
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showToast,
        validateEmail,
        validatePassword,
        makeAuthenticatedRequest,
        formatCurrency,
        formatDate,
        formatDateTime,
        debounce,
        throttle,
        copyToClipboard
    };
}

// ===== CSS ANIMATIONS INJECTION =====
const additionalCSS = `
@keyframes toastSlideOut {
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: hsl(var(--bg-primary) / 0.8);
    backdrop-filter: blur(5px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    color: hsl(var(--text-primary));
    font-size: 1.2rem;
}

.loading-spinner {
    border: 3px solid hsl(var(--border-primary));
    border-top: 3px solid hsl(var(--primary));
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
`;

// Inject additional CSS
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);

// Verificar autenticação ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    checkAuthenticationStatus();
    updateAuthenticationUI();

    // Configurar navegação mobile
    setupMobileNavigation();

    // Configurar tooltips
    setupTooltips();
});

function setupMobileNavigation() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });

        // Fechar menu ao clicar em link
        const navLinks = navMenu.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            });
        });
    }
}

function setupTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const text = event.target.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    document.body.appendChild(tooltip);

    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Função para verificar o status de autenticação
function checkAuthenticationStatus() {
    const token = localStorage.getItem('access_token');
    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');

    if (token && userData) {
        // Verificar se o token ainda é válido
        fetch('/api/license/check', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }).then(response => {
            if (response.status === 401) {
                // Token expirado
                logout();
            }
        }).catch(error => {
            console.log('Erro ao verificar token:', error);
        });
    }

    updateAuthenticationUI();
}

// Função para mostrar notificações
function showToast(message, type = 'info') {
    console.log('Mostrando toast:', message, type);

    // Remover toast anterior se existir
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Criar novo toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;

    // Adicionar estilos inline para garantir funcionamento
    const backgroundColor = type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : type === 'warning' ? '#F59E0B' : '#3B82F6';

    toast.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${backgroundColor};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 10001;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-weight: 500;
        font-size: 14px;
        max-width: 400px;
        animation: slideInRight 0.3s ease;
        border-left: 4px solid rgba(255,255,255,0.3);
    `;

    // Adicionar animação CSS se não existir
    if (!document.querySelector('#toast-animations')) {
        const style = document.createElement('style');
        style.id = 'toast-animations';
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            .toast-content {
                display: flex;
                align-items: center;
                gap: 10px;
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    // Remover após 5 segundos
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, 5000);

    // Permitir fechar clicando no toast
    toast.addEventListener('click', () => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    });
}

// Função para logout
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    updateAuthenticationUI();
    showToast('Logout realizado com sucesso', 'success');

    // Redirecionar para home se estiver em página protegida
    const protectedPages = ['/painel', '/admin'];
    if (protectedPages.some(page => window.location.pathname.includes(page))) {
        window.location.href = '/';
    }
}

// Atualizar interface baseada no status de autenticação
function updateAuthenticationUI() {
    const token = localStorage.getItem('access_token');
    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');

    const loginLink = document.getElementById('loginLink');
    const logoutLink = document.getElementById('logoutLink');
    const painelLink = document.getElementById('painelLink');
    const adminLink = document.getElementById('adminLink');

    if (token && userData.email) {
        // Usuário logado
        if (loginLink) loginLink.style.display = 'none';
        if (logoutLink) logoutLink.style.display = 'block';
        if (painelLink) painelLink.style.display = 'block';

        // Mostrar link admin apenas para admins
        if (adminLink) {
            adminLink.style.display = userData.is_admin ? 'block' : 'none';
        }
    } else {
        // Usuário não logado
        if (loginLink) loginLink.style.display = 'block';
        if (logoutLink) logoutLink.style.display = 'none';
        if (painelLink) painelLink.style.display = 'none';
        if (adminLink) adminLink.style.display = 'none';
    }
}