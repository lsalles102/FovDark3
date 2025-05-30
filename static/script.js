// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 FovDark System Initialized');

    try {
        // Verificar se estamos em uma página válida
        if (!document.body) {
            console.error('❌ Body não encontrado, aguardando...');
            setTimeout(() => {
                if (document.body) {
                    document.dispatchEvent(new Event('DOMContentLoaded'));
                }
            }, 100);
            return;
        }

        // Inicializar componentes em ordem
        initializeApp();
        setupNavigation();
        setupToastContainer();

        // Verificar autenticação após um pequeno delay
        setTimeout(() => {
            checkAuthenticationStatus();
        }, 100);

    } catch (error) {
        console.error('❌ Erro na inicialização:', error);
    }
});

// ===== GLOBAL VARIABLES =====
let currentUser = null;
let isAuthenticated = false;
let authToken = null;

// ===== UTILITY FUNCTIONS =====
function initializeApp() {
    console.log('🔧 Inicializando aplicação...');

    // Recuperar token do localStorage
    authToken = localStorage.getItem('authToken');
    if (authToken) {
        isAuthenticated = true;
        console.log('✅ Token encontrado no localStorage');
    }

    // Inicializar componentes específicos da página
    const currentPage = window.location.pathname;
    console.log(`📍 Página atual: ${currentPage}`);

    switch(currentPage) {
        case '/login':
            initializeLoginPage();
            break;
        case '/register':
            initializeRegisterPage();
            break;
        case '/painel':
            initializePainelPage();
            break;
        case '/comprar':
            initializeComprarPage();
            break;
        case '/admin':
            initializeAdminPage();
            break;
        default:
            initializeHomePage();
    }
}

function setupNavigation() {
    console.log('🧭 Configurando navegação...');

    // Mobile menu toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
    }

    // Smooth scrolling para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function setupToastContainer() {
    if (!document.querySelector('.toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
}

// ===== AUTHENTICATION FUNCTIONS =====
function checkAuthenticationStatus() {
    console.log('🔐 Verificando status de autenticação...');

    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');

    if (token && userData) {
        try {
            currentUser = JSON.parse(userData);
            isAuthenticated = true;
            authToken = token;

            console.log('✅ Usuário autenticado:', currentUser.email);
            updateNavigationForAuthenticatedUser();

            // Verificar se o token ainda é válido
            validateToken();

        } catch (error) {
            console.error('❌ Erro ao processar dados do usuário:', error);
            logout();
        }
    } else {
        console.log('❌ Usuário não autenticado');
        updateNavigationForUnauthenticatedUser();
    }
}

function updateNavigationForAuthenticatedUser() {
    console.log('🔄 Atualizando navegação para usuário autenticado');

    // Atualizar botões de login/logout na navegação
    const loginBtn = document.querySelector('.nav-menu .login-btn');
    const registerBtn = document.querySelector('.nav-menu .register-btn');

    if (loginBtn) {
        loginBtn.style.display = 'none';
    }

    if (registerBtn) {
        registerBtn.style.display = 'none';
    }

    // Adicionar botão de logout se não existir
    let logoutBtn = document.querySelector('.logout-btn');
    if (!logoutBtn) {
        logoutBtn = document.createElement('a');
        logoutBtn.href = '#';
        logoutBtn.className = 'nav-link logout-btn';
        logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i> Logout';
        logoutBtn.addEventListener('click', logout);

        const navMenu = document.querySelector('.nav-menu');
        if (navMenu) {
            navMenu.appendChild(logoutBtn);
        }
    }

    logoutBtn.style.display = 'block';

    // Mostrar link do painel
    let painelBtn = document.querySelector('.painel-btn');
    if (!painelBtn) {
        painelBtn = document.createElement('a');
        painelBtn.href = '/painel';
        painelBtn.className = 'nav-link painel-btn';
        painelBtn.innerHTML = '<i class="fas fa-user-circle"></i> Painel';

        const navMenu = document.querySelector('.nav-menu');
        if (navMenu) {
            navMenu.insertBefore(painelBtn, logoutBtn);
        }
    }

    painelBtn.style.display = 'block';

    // Mostrar link admin se for admin
    if (currentUser && currentUser.is_admin) {
        let adminBtn = document.querySelector('.admin-btn');
        if (!adminBtn) {
            adminBtn = document.createElement('a');
            adminBtn.href = '/admin';
            adminBtn.className = 'nav-link admin-btn';
            adminBtn.innerHTML = '<i class="fas fa-cog"></i> Admin';

            const navMenu = document.querySelector('.nav-menu');
            if (navMenu) {
                navMenu.insertBefore(adminBtn, painelBtn);
            }
        }
        adminBtn.style.display = 'block';
    }
}

function updateNavigationForUnauthenticatedUser() {
    console.log('🔄 Atualizando navegação para usuário não autenticado');

    // Mostrar botões de login/register
    const loginBtn = document.querySelector('.nav-menu .login-btn');
    const registerBtn = document.querySelector('.nav-menu .register-btn');

    if (loginBtn) loginBtn.style.display = 'block';
    if (registerBtn) registerBtn.style.display = 'block';

    // Esconder botões autenticados
    const logoutBtn = document.querySelector('.logout-btn');
    const painelBtn = document.querySelector('.painel-btn');
    const adminBtn = document.querySelector('.admin-btn');

    if (logoutBtn) logoutBtn.style.display = 'none';
    if (painelBtn) painelBtn.style.display = 'none';
    if (adminBtn) adminBtn.style.display = 'none';
}

async function validateToken() {
    if (!authToken) return false;

    try {
        const response = await fetch('/api/license/check', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            console.log('✅ Token válido');
            return true;
        } else {
            console.log('❌ Token inválido, fazendo logout');
            logout();
            return false;
        }
    } catch (error) {
        console.error('❌ Erro ao validar token:', error);
        return false;
    }
}

function logout() {
    console.log('🚪 Fazendo logout...');

    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');

    currentUser = null;
    isAuthenticated = false;
    authToken = null;

    updateNavigationForUnauthenticatedUser();

    showToast('Logout realizado com sucesso!', 'success');

    // Redirecionar para home se estiver em página protegida
    const protectedPages = ['/painel', '/admin'];
    if (protectedPages.includes(window.location.pathname)) {
        window.location.href = '/';
    }
}

// ===== PAGE INITIALIZATION FUNCTIONS =====
function initializeHomePage() {
    console.log('🏠 Inicializando página inicial...');
    // Adicionar animações ou funcionalidades específicas da home
}

function initializeLoginPage() {
    console.log('🔐 Inicializando página de login...');

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

function initializeRegisterPage() {
    console.log('📝 Inicializando página de registro...');

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
}

function initializePainelPage() {
    console.log('👤 Inicializando painel do usuário...');

    // Verificar se está autenticado
    if (!isAuthenticated) {
        window.location.href = '/login';
        return;
    }

    loadUserData();
}

function initializeComprarPage() {
    console.log('🛒 Inicializando página de compras...');
    loadProducts();
}

function initializeAdminPage() {
    console.log('⚙️ Inicializando painel administrativo...');

    // Verificar se é admin
    if (!currentUser || !currentUser.is_admin) {
        window.location.href = '/';
        return;
    }

    loadAdminData();
}

// ===== FORM HANDLERS =====
async function handleLogin(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');

    try {
        setButtonLoading(submitBtn, true);

        const response = await fetch('/api/login', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('userData', JSON.stringify(data.user));

            currentUser = data.user;
            isAuthenticated = true;
            authToken = data.access_token;

            showToast('Login realizado com sucesso!', 'success');

            setTimeout(() => {
                window.location.href = '/painel';
            }, 1000);

        } else {
            showToast(data.detail || 'Erro no login', 'error');
        }

    } catch (error) {
        console.error('Erro no login:', error);
        showToast('Erro de conexão', 'error');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

async function handleRegister(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');

    try {
        setButtonLoading(submitBtn, true);

        const response = await fetch('/api/register', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Conta criada com sucesso! Faça login para continuar.', 'success');

            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);

        } else {
            showToast(data.detail || 'Erro no registro', 'error');
        }

    } catch (error) {
        console.error('Erro no registro:', error);
        showToast('Erro de conexão', 'error');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

// ===== DATA LOADING FUNCTIONS =====
async function loadUserData() {
    if (!authToken) return;

    try {
        const response = await fetch('/api/license/check', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            updateUserInterface(data);
        }

    } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
    }
}

async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        const products = await response.json();

        displayProducts(products);

    } catch (error) {
        console.error('Erro ao carregar produtos:', error);
        showToast('Erro ao carregar produtos', 'error');
    }
}

async function loadAdminData() {
    if (!authToken) return;

    try {
        const [usersResponse, paymentsResponse] = await Promise.all([
            fetch('/api/admin/users', {
                headers: { 'Authorization': `Bearer ${authToken}` }
            }),
            fetch('/api/admin/payments', {
                headers: { 'Authorization': `Bearer ${authToken}` }
            })
        ]);

        if (usersResponse.ok && paymentsResponse.ok) {
            const users = await usersResponse.json();
            const payments = await paymentsResponse.json();

            displayAdminData(users, payments);
        }

    } catch (error) {
        console.error('Erro ao carregar dados admin:', error);
    }
}

// ===== UI UPDATE FUNCTIONS =====
function updateUserInterface(userData) {
    // Implementar atualização da interface com dados do usuário
    console.log('Dados do usuário:', userData);
}

function displayProducts(products) {
    const container = document.querySelector('.products-container');
    if (!container) return;

    container.innerHTML = products.map(product => `
        <div class="product-card">
            <h3>${product.name}</h3>
            <p>${product.description}</p>
            <p class="price">R$ ${product.price}</p>
            <button onclick="buyProduct(${product.id})" class="btn btn-primary">
                Comprar
            </button>
        </div>
    `).join('');
}

function displayAdminData(users, payments) {
    // Implementar exibição de dados administrativos
    console.log('Usuários:', users);
    console.log('Pagamentos:', payments);
}

// ===== UTILITY FUNCTIONS =====
function showToast(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-message">${message}</span>
            <button class="toast-close">&times;</button>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, duration);

    // Manual close
    toast.querySelector('.toast-close').addEventListener('click', () => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    });
}

function setButtonLoading(button, loading) {
    if (!button) return;

    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || 'Enviar';
    }
}

// ===== API FUNCTIONS =====
async function buyProduct(productId) {
    if (!isAuthenticated) {
        showToast('Faça login para comprar', 'warning');
        window.location.href = '/login';
        return;
    }

    try {
        const response = await fetch('/api/mercadopago/create-payment', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: productId
            })
        });

        const data = await response.json();

        if (response.ok) {
            window.location.href = data.payment_url;
        } else {
            showToast(data.detail || 'Erro ao processar pagamento', 'error');
        }

    } catch (error) {
        console.error('Erro ao comprar produto:', error);
        showToast('Erro de conexão', 'error');
    }
}

// ===== GLOBAL ERROR HANDLER =====
window.addEventListener('error', function(event) {
    console.error('❌ Erro JavaScript:', event.error);
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('❌ Promise rejeitada:', event.reason);
});

// ===== GLOBAL VARIABLES =====
let toastContainer;
let navToggle;
let navMenu;

// ===== FORM UTILITIES =====
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
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
function displayPurchaseProducts(products, container) {
    container.innerHTML = '';
    products.forEach(product => {
        const productCard = createProductCard(product);
        container.appendChild(productCard);
    });
}

function displayAdminProducts(products, container) {
    container.innerHTML = products.map(product => {
        const statusClass = product.is_active ? 'status-active' : 'status-inactive';
        const statusText = product.is_active ? 'Ativo' : 'Inativo';
        const statusIcon = product.is_active ? 'fas fa-check-circle' : 'fas fa-times-circle';

        const priceFormatted = new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(product.price);

        const featuresArray = product.features ?
            (typeof product.features === 'string' ? product.features.split(',') : product.features) : [];
        const featuresHTML = featuresArray.slice(0, 3).map(feature =>
            `<span class="feature-tag">${feature.trim()}</span>`
        ).join('');

        return `
            <div class="product-admin-card">
                <div class="product-card-header">
                    <div class="product-status ${statusClass}">
                        <i class="${statusIcon}"></i>
                        <span>${statusText}</span>
                    </div>
                    <div class="product-id">#${product.id}</div>
                </div>

                <div class="product-card-image">
                    ${product.image_url ?
                        `<img src="${product.image_url}" alt="${product.name}" onerror="this.src='/static/hero-bg.jpg'">` :
                        `<div class="no-image"><i class="fas fa-image"></i></div>`
                    }
                </div>

                <div class="product-card-content">
                    <h3 class="product-card-title">${product.name}</h3>
                    <p class="product-card-description">${product.description || 'Sem descrição'}</p>

                    <div class="product-features">
                        ${featuresHTML}
                        ${featuresArray.length > 3 ? `<span class="feature-more">+${featuresArray.length - 3}</span>` : ''}
                    </div>

                    <div class="product-card-info">
                        <div class="info-item">
                            <span class="label">Preço:</span>
                            <span class="value price">${priceFormatted}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Duração:</span>
                            <span class="value">${product.duration_days} dias</span>
                        </div>
                    </div>
                </div>

                <div class="product-card-actions">
                    <button class="btn-action btn-edit" onclick="editProduct(${product.id})" title="Editar Produto">
                        <i class="fas fa-edit"></i>
                        <span>Editar</span>
                    </button>
                    <button class="btn-action btn-delete" onclick="confirmDeleteProduct(${product.id})" title="Deletar Produto">
                        <i class="fas fa-trash"></i>
                        <span>Deletar</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
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
        console.log('💾 Storage mudou:', e.key);
        if (e.key === 'access_token' || e.key === 'user_data') {
            console.log('🔄 Dados de autenticação mudaram, atualizando UI');
            setTimeout(() => {
                updateAuthenticationUI();
            }, 100);
        }
    });

    // Verificar autenticação quando a página ganha foco
    window.addEventListener('focus', function() {
        console.log('👁️ Página ganhou foco, verificando autenticação');
        setTimeout(() => {
            updateAuthenticationUI();
            checkAuthenticationStatus();
        }, 200);
    });

    // Verificar autenticação quando a página se torna visível
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            console.log('👁️ Página se tornou visível, verificando autenticação');
            setTimeout(() => {
                updateAuthenticationUI();
                checkAuthenticationStatus();
            }, 200);
        }
    });

    // Verificação periódica de autenticação (a cada 30 segundos)
    setInterval(function() {
        const token = localStorage.getItem('access_token');
        if (token) {
            console.log('⏰ Verificação periódica de autenticação');
            checkAuthenticationStatus();
        }
    }, 30000); // 30 segundos

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

// The code integrates MercadoPago payment processing, loads product data from an API, and displays products on the page with the option to purchase.
async function selectPlan(productId, productPrice, planName, durationDays) {
    const token = localStorage.getItem('access_token');

    if (!token) {
        showToast('Você precisa estar logado para comprar', 'error');
        setTimeout(() => {
            window.location.href = '/login';
        }, 1000);
        return;
    }

    console.log(`✨ Iniciando checkout para o plano: ${planName} (ID: ${productId})`);
    console.log('💰 Preço:', productPrice);
    console.log('⏳ Duração:', durationDays, 'dias');

    try {
        // Criar checkout no Mercado Pago
        const checkoutData = {
            plano: productId || planName,
            product_id: productId
        };

        console.log('🛒 Enviando dados de checkout:', checkoutData);

        const response = await fetch('/api/criar-checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify(checkoutData)
        });

        if (!response.ok) {
            const errorBody = await response.text();
            console.error('❌ Erro ao criar checkout:', response.status, errorBody);
            showToast(`Erro ao criar checkout: ${response.status} - ${errorBody}`, 'error');
            return;
        }

        const data = await response.json();
        console.log('🎁 Resposta do checkout:', data);

        if (data && data.init_point) {
            // Redirecionar para o Mercado Pago
            console.log('📍 Redirecionando para:', data.init_point);
            window.location.href = data.init_point;
        } else {
            console.error('❌ Link de checkout inválido');
            showToast('Erro ao obter link de pagamento', 'error');
        }

    } catch (error) {
        console.error('💥 Erro geral no checkout:', error);
        showToast('Erro ao processar pagamento', 'error');
    }
}