// ===== GLOBAL VARIABLES =====
let toastContainer;
let navToggle;
let navMenu;

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 FovDark System Initialized');
    initializeApp();
    setupNavigation();
    setupToastContainer();
    checkAuthenticationStatus();
    setupGlobalEventListeners();
});

// ===== APP INITIALIZATION =====
function initializeApp() {
    // Add loading animations to cards
    animateElements();

    // Setup auth state
    updateAuthenticationUI();

    // Load products if on purchase page
    if (window.location.pathname === '/comprar') {
        loadProducts();
    }
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
    if (navMenu && navToggle) {
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

        // Lista de emails autorizados como admin
        const AUTHORIZED_ADMIN_EMAILS = [
            'admin@fovdark.com',
            'lsalles102@gmail.com'
        ];

        // Verificar se é admin autorizado
        const userEmailLower = userData.email.toLowerCase().trim();
        const isAuthorizedAdmin = AUTHORIZED_ADMIN_EMAILS.some(email => 
            email.toLowerCase() === userEmailLower
        );

        // Mostrar menu admin apenas se for autorizado E se is_admin for true
        const adminMenuLink = document.querySelector('.nav-link[href="/admin"]');
        if (adminMenuLink) {
            if (isAuthorizedAdmin && userData.is_admin) {
                adminMenuLink.style.display = 'flex';
            } else {
                adminMenuLink.style.display = 'none';
            }
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
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10001;
            pointer-events: none;
        `;
        document.body.appendChild(toastContainer);
    }
}

function showToast(message, type = 'info', duration = 5000) {
    if (!toastContainer) {
        setupToastContainer();
    }

    // Remover toast anterior se existir
    const existingToast = toastContainer.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };

    const colors = {
        success: '#10B981',
        error: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6'
    };

    toast.innerHTML = `
        <div class="toast-content">
            <i class="${icons[type] || icons.info}"></i>
            <span>${message}</span>
        </div>
    `;

    toast.style.cssText = `
        background: ${colors[type] || colors.info};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-weight: 500;
        font-size: 14px;
        max-width: 400px;
        animation: slideInRight 0.3s ease;
        border-left: 4px solid rgba(255,255,255,0.3);
        pointer-events: auto;
        cursor: pointer;
    `;

    // Adicionar estilos de animação se não existirem
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

    toastContainer.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        removeToast(toast);
    }, duration);

    // Click to remove
    toast.addEventListener('click', () => {
        removeToast(toast);
    });
}

function removeToast(toast) {
    if (toast && toast.parentElement) {
        toast.style.animation = 'slideOutRight 0.3s ease';
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

// ===== LOGIN FUNCTION =====
async function login(event) {
    if (event) {
        event.preventDefault();
    }

    console.log('🔐 Iniciando processo de login');

    const emailField = document.getElementById('email');
    const passwordField = document.getElementById('password');

    if (!emailField || !passwordField) {
        showToast('Campos de login não encontrados', 'error');
        return;
    }

    const email = emailField.value.trim();
    const password = passwordField.value;

    // Validações
    if (!email || !password) {
        showToast('Preencha todos os campos', 'error');
        return;
    }

    if (!validateEmail(email)) {
        showToast('Email inválido', 'error');
        return;
    }

    const submitBtn = document.querySelector('button[type="submit"]') || document.getElementById('login-btn');
    if (!submitBtn) {
        showToast('Botão de login não encontrado', 'error');
        return;
    }

    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> CONECTANDO...';
    submitBtn.disabled = true;

    try {
        console.log('📡 Enviando requisição de login');

        const formData = new FormData();
        formData.append('email', email);
        formData.append('password', password);

        const response = await fetch('/api/login', {
            method: 'POST',
            body: formData
        });

        console.log('📥 Resposta recebida:', response.status);

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
        console.log('✅ Login bem-sucedido:', data);

        if (data.access_token && data.user) {
            // Salvar dados do usuário
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_data', JSON.stringify(data.user));

            showToast('Login realizado com sucesso!', 'success');
            updateAuthenticationUI();

            // Verificar redirecionamento
            const urlParams = new URLSearchParams(window.location.search);
            const redirect = urlParams.get('redirect');

            setTimeout(() => {
                if (redirect === 'comprar') {
                    window.location.href = '/comprar?from=login';
                } else if (data.user && data.user.is_admin) {
                    window.location.href = '/admin';
                } else {
                    window.location.href = '/painel';
                }
            }, 1000);

            return data;
        } else {
            throw new Error('Dados de resposta inválidos');
        }

    } catch (error) {
        console.error('❌ Erro no login:', error);
        showToast(error.message || 'Erro inesperado no login', 'error');
        throw error;
    } finally {
        // Restaurar botão
        if (submitBtn) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
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

// ===== PRODUCTS =====
async function loadProducts() {
    try {
        console.log('📦 Carregando produtos...');
        const response = await fetch('/api/products');

        if (response.ok) {
            const products = await response.json();
            console.log('✅ Produtos carregados:', products);
            displayProducts(products);
        } else {
            console.error('❌ Erro ao carregar produtos:', response.status);
            showToast('Erro ao carregar produtos', 'error');
        }
    } catch (error) {
        console.error('💥 Erro de conexão:', error);
        showToast('Erro de conexão ao carregar produtos', 'error');
    }
}

function displayProducts(products) {
    const container = document.querySelector('.pricing-grid');
    if (!container) {
        console.warn('⚠️ Container de produtos não encontrado');
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

    container.innerHTML = '';
    products.forEach(product => {
        const productCard = createProductCard(product);
        container.appendChild(productCard);
    });
}

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

// ===== GLOBAL EVENT LISTENERS =====
function setupGlobalEventListeners() {
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
            const element = document.getElementById(targetId);
            if (element) {
                element.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
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

// ===== UTILITY FUNCTIONS =====
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

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text).then(() => {
            showToast('Copiado para a área de transferência', 'success');
        });
    } else {
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

// ===== PURCHASE FUNCTIONS =====
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

function selectPlan(productId, price, planName, durationDays) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showToast('Você precisa estar logado para comprar', 'error');
        window.location.href = '/login?redirect=comprar';
        return;
    }

    // Processar pagamento diretamente
    processPayment(productId);
}

// ===== FAQ FUNCTIONS =====
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
            if (otherAnswer) otherAnswer.style.maxHeight = '0';
            if (otherIcon) otherIcon.style.transform = 'rotate(0deg)';
        }
    });

    // Toggle atual
    const isActive = faqItem.classList.contains('active');

    if (isActive) {
        faqItem.classList.remove('active');
        if (answer) answer.style.maxHeight = '0';
        if (icon) icon.style.transform = 'rotate(0deg)';
    } else {
        faqItem.classList.add('active');
        if (answer) {
            const scrollHeight = answer.scrollHeight;
            answer.style.maxHeight = scrollHeight + 'px';
        }
        if (icon) icon.style.transform = 'rotate(180deg)';
    }
}

// ===== EXTERNAL LINKS =====
function openExternalLink(url, platform) {
    window.open(url, '_blank');
    console.log(`🔗 Link externo aberto: ${platform} - ${url}`);
}

// ===== SSL CHECK =====
function checkSSL() {
    if (location.protocol === 'https:') {
        console.log('✅ Conexão SSL Segura');
        return true;
    } else {
        console.warn('⚠️ Conexão não segura');
        return false;
    }
}

// ===== INITIALIZATION =====
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

console.log('✅ FovDark Script carregado com sucesso');

function updateUserInfo(user) {
    const userInfo = document.querySelector('.user-info');
    if (userInfo) {
        // Lista de emails autorizados como admin
        const AUTHORIZED_ADMIN_EMAILS = [
            'admin@fovdark.com',
            'lsalles102@gmail.com'
        ];

        // Verificar se o email está na lista de autorizados (case-insensitive)
        const userEmailLower = user.email.toLowerCase().trim();
        const isAuthorizedAdmin = AUTHORIZED_ADMIN_EMAILS.some(email => 
            email.toLowerCase() === userEmailLower
        );

        // Mostrar badge apenas se for autorizado E se is_admin for true
        const adminBadge = (isAuthorizedAdmin && user.is_admin) ? '<span class="admin-badge">ADMIN</span>' : '';

        userInfo.innerHTML = `
            <div class="user-avatar">${user.email.charAt(0).toUpperCase()}</div>
            <div class="user-details">
                <div class="user-email">${user.email} ${adminBadge}</div>
                <div class="user-since">Membro desde ${new Date().getFullYear()}</div>
            </div>
        `;
    }
}