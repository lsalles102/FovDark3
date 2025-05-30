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

    // Load products if on purchase page and products container exists
    if (window.location.pathname === '/comprar' && document.getElementById('productsGrid')) {
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

async function login(e) {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('login-btn');

    console.log('🔄 Iniciando processo de login...');

    // Validações básicas
    if (!email || !password) {
        showToast('Por favor, preencha todos os campos', 'error');
        return;
    }

    // Validar formato do email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showToast('Por favor, insira um email válido', 'error');
        return;
    }

    // Estado de loading
    const originalText = loginBtn.innerHTML;
    loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>ENTRANDO...</span>';
    loginBtn.disabled = true;

    try {
        console.log('📧 Email:', email);

        // Preparar dados do formulário
        const formData = new FormData();
        formData.append('email', email);
        formData.append('password', password);

        const response = await fetch('/api/login', {
            method: 'POST',
            body: formData
        });

        console.log('📡 Status da resposta:', response.status);

        const data = await response.json();
        console.log('📊 Dados recebidos:', data);

        if (response.ok && data.access_token) {
            console.log('✅ Login bem-sucedido!');

            // Salvar dados no localStorage
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_data', JSON.stringify(data.user));

            showToast('Login realizado com sucesso!', 'success');

            // Aguardar um pouco antes do redirecionamento
            setTimeout(() => {
                if (data.user.is_admin) {
                    console.log('👑 Redirecionando admin para /admin');
                    window.location.href = '/admin';
                } else {
                    console.log('👤 Redirecionando usuário para /painel');
                    window.location.href = '/painel';
                }
            }, 1000);

        } else {
            console.log('❌ Erro no login:', data.detail || 'Erro desconhecido');
            showToast(data.detail || 'Email ou senha incorretos', 'error');
        }

    } catch (error) {
        console.error('💥 Erro na requisição:', error);
        showToast('Erro de conexão. Tente novamente.', 'error');
    } finally {
        // Restaurar botão
        loginBtn.innerHTML = originalText;
        loginBtn.disabled = false;
    }
}

function showToast(message, type = 'info') {
    // Remover toast anterior se existir
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Criar novo toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;

    // Adicionar estilos se não existirem
    if (!document.querySelector('#toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background: hsl(var(--bg-secondary));
                color: hsl(var(--text-primary));
                padding: 1rem 1.5rem;
                border-radius: var(--radius-md);
                border: 1px solid hsl(var(--border-primary));
                box-shadow: var(--shadow-lg);
                display: flex;
                align-items: center;
                gap: 0.5rem;
                z-index: 9999;
                animation: slideIn 0.3s ease-out;
            }

            .toast-success {
                border-color: hsl(var(--success));
                background: hsl(var(--success) / 0.1);
            }

            .toast-error {
                border-color: hsl(var(--danger));
                background: hsl(var(--danger) / 0.1);
            }

            .toast-success i {
                color: hsl(var(--success));
            }

            .toast-error i {
                color: hsl(var(--danger));
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    // Remover após 5 segundos
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// Função para validar email
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Função para validar senha
function validatePassword(password) {
    return password && password.length >= 8;
}

// Função para sanitizar entrada
function sanitizeInput(input) {
    if (typeof input !== 'string') return '';
    return input.trim().replace(/[<>&"']/g, function(match) {
        const entities = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            "'": '&#x27;'
        };
        return entities[match];
    });
}

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
                console.log('🔄 Token expirado, fazendo logout');
                logout();
            } else if (!response.ok) {
                console.log('⚠️ Erro na verificação, mas não é 401:', response.status);
                // Não fazer logout em caso de erro de servidor
            }
        }).catch(error => {
            console.log('❌ Erro de rede ao verificar token:', error);
            // Não fazer logout em caso de erro de rede
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

        // Mostrar/ocultar link admin
        if (adminLink) {
            adminLink.style.display = isAuthorizedAdmin ? 'flex' : 'none';
        }
    } else {
        // Usuário não logado
        if (loginLink) loginLink.style.display = 'flex';
        if (logoutLink) logoutLink.style.display = 'none';
        if (painelLink) painelLink.style.display = 'none';
        if (adminLink) adminLink.style.display = 'none';
    }
}

// Função para fazer requisições com timeout
async function fetchWithTimeout(url, options = {}, timeout = 10000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Timeout: A requisição demorou muito para responder');
        }
        throw error;
    }
}

// Função para mostrar loading
function showLoading(element, text = 'Carregando...') {
    if (!element) return;

    const originalContent = element.innerHTML;
    element.innerHTML = `
        <div class="loading-content">
            <div class="spinner"></div>
            <span>${text}</span>
        </div>
    `;
    element.disabled = true;
    element.dataset.originalContent = originalContent;
}

// Função para esconder loading
function hideLoading(element) {
    if (!element || !element.dataset.originalContent) return;

    element.innerHTML = element.dataset.originalContent;
    element.disabled = false;
    delete element.dataset.originalContent;
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
    event.preventDefault();

    const loginBtn = document.getElementById('login-btn');
    const originalText = loginBtn.innerHTML;

    loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>CONECTANDO...</span>';
    loginBtn.disabled = true;

    console.log('🔐 Iniciando processo de login');

    try {
        const formData = new FormData();
        formData.append('email', document.getElementById('email').value);
        formData.append('password', document.getElementById('password').value);

        console.log('📡 Enviando requisição de login');

        const response = await fetch('/api/login', {
            method: 'POST',
            body: formData
        });

        console.log('📥 Resposta recebida:', response.status);

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Erro no login');
        }

        console.log('✅ Login bem-sucedido:', data);

        // Armazenar token e dados do usuário
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user_data', JSON.stringify(data.user));

        // Mostrar sucesso temporariamente
        loginBtn.innerHTML = '<i class="fas fa-check"></i> <span>SUCESSO!</span>';
        loginBtn.style.background = 'linear-gradient(135deg, #00d4ff, #1e90ff)';

        // Redirecionamento baseado no tipo de usuário com verificação adicional
        setTimeout(() => {
            if (data.user && data.user.is_admin === true) {
                console.log('👑 Redirecionando admin para /admin');
                window.location.href = '/admin';
            } else {
                console.log('👤 Redirecionando usuário para /painel');
                window.location.href = '/painel';
            }
        }, 500);

    } catch (error) {
        console.error('❌ Erro no login:', error);

        loginBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> <span>ERRO!</span>';
        loginBtn.style.background = 'linear-gradient(135deg, #ff4757, #ff3742)';

        // Mostrar erro específico
        const errorMessage = error.message === 'Email ou senha incorretos' 
            ? 'Credenciais inválidas' 
            : 'Erro de conexão';

        showNotification(errorMessage, 'error');

        // Restaurar botão após 2 segundos
        setTimeout(() => {
            loginBtn.innerHTML = originalText;
            loginBtn.style.background = '';
            loginBtn.disabled = false;
        }, 2000);
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
    // Tentar encontrar o container correto
    let container = document.getElementById('productsGrid');
    if (!container) {
        container = document.getElementById('productsAdminGrid');
    }

    if (!container) {
        console.warn('⚠️ Container de produtos não encontrado em', window.location.pathname);
        return;
    }

    try {
        console.log('📦 Carregando produtos...');
        console.log('🌐 URL da requisição:', '/api/products');

        // Mostrar loading
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 1rem; color: var(--primary);"></i>
                <h3>Carregando produtos...</h3>
            </div>
        `;

        const response = await fetch('/api/products');
        console.log('📡 Status da resposta:', response.status, response.statusText);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Erro HTTP:', response.status, errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }

        const responseText = await response.text();
        console.log('📥 Resposta bruta:', responseText);

        let products;
        try {
            products = JSON.parse(responseText);
        } catch (parseError) {
            console.error('❌ Erro ao fazer parse do JSON:', parseError);
            throw new Error('Resposta não é um JSON válido');
        }

        console.log('✅ Produtos carregados:', products);
        console.log('🔍 Tipo da resposta:', typeof products, 'É array?', Array.isArray(products));

        // Verificar se products é um array
        if (!Array.isArray(products)) {
            console.error('❌ Products não é um array:', products);
            throw new Error('Resposta inválida: produtos não é um array');
        }

        displayProducts(products);

    } catch (error) {
        console.error('💥 Erro ao carregar produtos:', error);

        if (container) {
            const errorMessage = error.message.includes('HTTP') ? 
                `Erro ${error.message}` : 
                'Erro de conexão';

            container.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem; color: var(--danger);"></i>
                    <h3>${errorMessage}</h3>
                    <p>Tente recarregar a página ou entre em contato com o suporte.</p>
                    <button onclick="loadProducts()" style="
                        margin-top: 1rem;
                        padding: 0.5rem 1rem;
                        background: var(--primary);
                        color: white;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 600;
                    ">
                        <i class="fas fa-sync-alt"></i> Tentar Novamente
                    </button>
                </div>
            `;
        }
    }
}

function displayProducts(products) {
    // Tentar encontrar o container correto dependendo da página
    let container = document.getElementById('productsGrid');

    // Se não encontrar, tentar outros possíveis IDs
    if (!container) {
        container = document.getElementById('productsAdminGrid');
    }

    if (!container) {
        console.warn('⚠️ Container de produtos não encontrado em', window.location.pathname);
        return;
    }

    console.log('✅ Container encontrado, exibindo produtos:', products);

    if (!Array.isArray(products)) {
        console.error('❌ Products não é um array:', products);
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem; color: var(--danger);"></i>
                <h3>Erro no formato dos dados</h3>
                <p>Dados dos produtos em formato inválido.</p>
            </div>
        `;
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

    try {
        // Verificar se estamos na página de compras ou admin
        const isAdminPage = window.location.pathname.includes('/admin');

        if (isAdminPage) {
            // Usar função específica para admin
            displayAdminProducts(products, container);
        } else {
            // Usar função para página de compras
            displayPurchaseProducts(products, container);
        }
    } catch (error) {
        console.error('❌ Erro ao exibir produtos:', error);
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem; color: var(--danger);"></i>
                <h3>Erro ao exibir produtos</h3>
                <p>Tente recarregar a página.</p>
            </div>
        `;
    }
}

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
<///The code integrates MercadoPago payment processing, loads product data from an API, and displays products on the page with the option to purchase.
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