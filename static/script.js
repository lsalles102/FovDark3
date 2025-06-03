// ===== SISTEMA DE AUTENTICAÇÃO SIMPLIFICADO =====
(function() {
    console.log('🚀 Inicializando FovDark...');

    // ===== VARIÁVEIS GLOBAIS =====
    let currentUser = null;
    let isAuthenticated = false;

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function() {
        console.log('✅ DOM carregado');
        initializeApp();
    });

    function initializeApp() {
        try {
            setupNavigation();
            checkAuthentication();
            setupEventListeners();
            initializePage();
            console.log('🎯 Sistema inicializado com sucesso');
        } catch (error) {
            console.error('❌ Erro na inicialização:', error);
        }
    }

    // Global error handler
    window.addEventListener('error', function(e) {
        console.error('Erro global capturado:', e.error);
        return true; // Previne que o erro pare a execução
    });

    window.addEventListener('unhandledrejection', function(e) {
        console.error('Promise rejeitada não tratada:', e.reason);
        e.preventDefault(); // Previne que apareça no console como erro não tratado
    });

    // ===== AUTENTICAÇÃO =====
    async function checkAuthentication() {
    try {
        console.log('🔍 Verificando autenticação...');
        const token = localStorage.getItem('access_token');
        const userData = localStorage.getItem('user_data');

        if (!token) {
            console.log('❌ Token não encontrado');
            clearAuthData();
            updateNavigation(false);
            return;
        }

        // Se tem dados do usuário salvos, usar eles primeiro
        if (userData) {
            try {
                currentUser = JSON.parse(userData);
                isAuthenticated = true;
                updateNavigation(true);
                console.log('✅ Usando dados salvos do usuário:', currentUser.email);
                return;
            } catch (error) {
                console.error('❌ Erro ao processar dados salvos:', error);
            }
        }

        // Verificar token no servidor apenas se necessário
        try {
            const response = await fetch('/api/verify_token', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.valid) {
                    localStorage.setItem('user_data', JSON.stringify(data.user));
                    currentUser = data.user;
                    isAuthenticated = true;
                    updateNavigation(true);
                    console.log('✅ Usuário autenticado:', currentUser.email);
                } else {
                    console.log('❌ Token inválido');
                    clearAuthData();
                    updateNavigation(false);
                }
            } else {
                console.log('❌ Erro na verificação do token');
                clearAuthData();
                updateNavigation(false);
            }
        } catch (error) {
            console.error('❌ Erro na verificação de autenticação:', error);
            // Não limpar dados em caso de erro de rede
            if (currentUser) {
                console.log('🔄 Mantendo sessão devido a erro de rede');
                return;
            }
            clearAuthData();
            updateNavigation(false);
        }
return true;
    } catch (error) {
        console.error('❌ Erro na autenticação:', error);
        clearAuthData();
        return false;
    }
    } catch (globalError) {
        console.error('❌ Erro global na autenticação:', globalError);
        clearAuthData();
        return false;
    }
    }

    // ===== NAVEGAÇÃO =====
    function updateNavigation(authenticated) {
        const loginBtn = document.querySelector('.login-btn');
        const registerBtn = document.querySelector('.register-btn');
        const navMenu = document.querySelector('.nav-menu');

        if (authenticated && currentUser) {
            // Esconder botões de login/registro
            if (loginBtn) loginBtn.style.display = 'none';
            if (registerBtn) registerBtn.style.display = 'none';

            // Adicionar botões autenticados
            addAuthenticatedButtons(navMenu);
        } else {
            // Mostrar botões de login/registro
            if (loginBtn) loginBtn.style.display = 'flex';
            if (registerBtn) registerBtn.style.display = 'flex';

            // Remover botões autenticados
            removeAuthenticatedButtons();
        }
    }

    function addAuthenticatedButtons(navMenu) {
        if (!navMenu) return;

        // Remover botões existentes primeiro
        removeAuthenticatedButtons();

        // Botão do painel
        const painelBtn = document.createElement('a');
        painelBtn.href = '/painel';
        painelBtn.className = 'nav-link painel-btn';
        painelBtn.innerHTML = '<i class="fas fa-user-circle"></i><span>Painel</span>';
        navMenu.appendChild(painelBtn);

        // Botão admin se for admin
        if (currentUser && currentUser.is_admin) {
            const adminBtn = document.createElement('a');
            adminBtn.href = '/admin';
            adminBtn.className = 'nav-link admin-btn';
            adminBtn.innerHTML = '<i class="fas fa-cog"></i><span>Admin</span>';
            navMenu.appendChild(adminBtn);
        }

        // Botão logout
        const logoutBtn = document.createElement('a');
        logoutBtn.href = '#';
        logoutBtn.className = 'nav-link logout-btn';
        logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i><span>Logout</span>';
        logoutBtn.addEventListener('click', handleLogout);
        navMenu.appendChild(logoutBtn);
    }

    function removeAuthenticatedButtons() {
        const buttons = document.querySelectorAll('.painel-btn, .admin-btn, .logout-btn');
        buttons.forEach(btn => btn.remove());
    }

    // ===== LOGOUT =====
    function handleLogout(e) {
        e.preventDefault();

        console.log('🚪 Fazendo logout...');
        clearAuthData();
        showToast('Logout realizado com sucesso!', 'success');

        // Redirecionar se estiver em página protegida
        const protectedPages = ['/painel', '/admin'];
        if (protectedPages.includes(window.location.pathname)) {
            window.location.href = '/';
        } else {
            checkAuthentication(); // Atualizar UI
        }
    }

    function clearAuthData() {
        console.log('🧹 Limpando todos os dados de autenticação...');

        // Limpar localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');

        // Limpar sessionStorage também (caso tenha dados lá)
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('user_data');

        // Limpar variáveis globais
        currentUser = null;
        isAuthenticated = false;

        console.log('✅ Dados de autenticação limpos');
    }

    // ===== NAVEGAÇÃO MOBILE =====
    function setupNavigation() {
        const navToggle = document.querySelector('.nav-toggle');
        const navMenu = document.querySelector('.nav-menu');

        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
                navToggle.classList.toggle('active');
            });
        }
    }

    // ===== EVENTOS GLOBAIS =====
    function setupEventListeners() {
        // Fechar menu mobile ao clicar em link
        document.addEventListener('click', function(e) {
            const navLink = e.target.closest('.nav-link');
            const navMenu = document.querySelector('.nav-menu');
            const navToggle = document.querySelector('.nav-toggle');

            if (navLink && navMenu && navToggle) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });

        // Verificar mudanças no localStorage
        window.addEventListener('storage', function(e) {
            if (e.key === 'access_token' || e.key === 'user_data') {
                console.log('🔄 Dados de autenticação alterados externamente');
                checkAuthentication();
            }
        });

        // Verificação periódica para detectar mudanças
        setInterval(() => {
            const token = localStorage.getItem('access_token');
            const userData = localStorage.getItem('user_data');

            if (userData) {
                try {
                    const parsedData = JSON.parse(userData);
                    if (currentUser && currentUser.email !== parsedData.email) {
                        console.log('🔄 Mudança de usuário detectada na verificação periódica');
                        checkAuthentication();
                    }
                } catch (error) {
                    console.error('❌ Erro na verificação periódica:', error);
                }
            }
        }, 2000); // Verificar a cada 2 segundos
    }

    // ===== INICIALIZAÇÃO POR PÁGINA =====
    function initializePage() {
        const path = window.location.pathname;

        switch(path) {
            case '/login':
                initializeLoginPage();
                break;
            case '/register':
                initializeRegisterPage();
                break;
            case '/painel':
                initializePainelPage();
                break;
            case '/admin':
                initializeAdminPage();
                break;
            case '/comprar':
                initializeComprarPage();
                break;
        }
    }

    // ===== LOGIN =====
    function initializeLoginPage() {
        console.log('🔐 Inicializando página de login');

        // Redirecionar se já estiver logado
        if (isAuthenticated && currentUser) {
            console.log('👤 Usuário já logado, redirecionando...');
            redirectUser();
            return;
        }

        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', handleLogin);
        }
    }

    async function handleLogin(e) {
        e.preventDefault();

        const form = e.target;
        const email = form.email.value.trim();
        const password = form.password.value;
        const submitBtn = form.querySelector('button[type="submit"]');

        if (!email || !password) {
            showToast('Preencha todos os campos', 'error');
            return;
        }

        setLoading(submitBtn, true);

        try {
            // LIMPAR DADOS ANTIGOS ANTES DE FAZER O LOGIN
            console.log('🧹 Limpando dados de autenticação anteriores...');
            clearAuthData();

            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);

            const response = await fetch('/api/login', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                console.log('✅ Login bem-sucedido');

                // Salvar dados de forma simples
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user_data', JSON.stringify(data.user));

                console.log('✅ Dados salvos:', data.user.email);

                // Atualizar estado
                currentUser = data.user;
                isAuthenticated = true;

                // Redirecionar imediatamente
                if (data.user.is_admin) {
                    window.location.replace('/admin');
                } else {
                    window.location.replace('/painel');
                }

            } else {
                console.log('❌ Erro no login:', data.detail);
                showToast(data.detail || 'Erro no login', 'error');
            }

        } catch (error) {
            console.error('❌ Erro no login:', error);
            showToast('Erro de conexão', 'error');
        } finally {
            setLoading(submitBtn, false);
        }
    }

    // ===== REGISTRO =====
    function initializeRegisterPage() {
        console.log('📝 Inicializando página de registro');

        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', handleRegister);
        }
    }

    async function handleRegister(e) {
        e.preventDefault();

        const form = e.target;
        const email = form.email.value.trim();
        const password = form.password.value;
        const confirmPassword = form.confirm_password.value;
        const submitBtn = form.querySelector('button[type="submit"]');

        if (password !== confirmPassword) {
            showToast('Senhas não coincidem', 'error');
            return;
        }

        if (password.length < 8) {
            showToast('Senha deve ter pelo menos 8 caracteres', 'error');
            return;
        }

        setLoading(submitBtn, true);

        try {
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);
            formData.append('confirm_password', confirmPassword);

            const response = await fetch('/api/register', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showToast('Conta criada com sucesso! Redirecionando...', 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                showToast(data.detail || 'Erro no registro', 'error');
            }

        } catch (error) {
            console.error('❌ Erro no registro:', error);
            showToast('Erro de conexão', 'error');
        } finally {
            setLoading(submitBtn, false);
        }
    }

    // ===== PÁGINAS PROTEGIDAS =====
    function initializePainelPage() {
        if (!isAuthenticated) {
            window.location.href = '/login';
            return;
        }
        console.log('👤 Inicializando painel do usuário');
    }

    function initializeAdminPage() {
        if (!isAuthenticated || !currentUser?.is_admin) {
            window.location.href = '/';
            return;
        }
        console.log('⚙️ Inicializando painel administrativo');
    }

    function initializeComprarPage() {
        console.log('🛒 Inicializando página de compras');
        loadProducts();
    }

    // ===== PRODUTOS =====
    async function loadProducts() {
        try {
            const response = await fetch('/api/products');
            const products = await response.json();

            const container = document.querySelector('.pricing-plans');
            if (container && products.length > 0) {
                displayProducts(products, container);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar produtos:', error);
        }
    }

    function displayProducts(products, container) {
        console.log('🎨 Renderizando produtos:', products);

        container.innerHTML = products.map(product => {
            console.log('🔧 Processando produto:', product.id, product.name);

            const features = product.features || [];
            const featuresHTML = features.map(feature => 
                `<li><i class="fas fa-check"></i>${feature.trim()}</li>`
            ).join('');

            // Garantir que o ID do produto seja válido
            const productId = product.id || 0;
            const productPrice = product.price || 0;
            const productName = (product.name || 'Produto').replace(/'/g, "\\'");
            const durationDays = product.duration_days || 30;

            return `
                <div class="pricing-plan ${product.is_featured ? 'featured' : ''}">
                    ${product.is_featured ? '<div class="plan-badge">RECOMENDADO</div>' : ''}
                    <div class="plan-header">
                        <h3 class="plan-name">${product.name}</h3>
                        <div class="plan-price">
                            <span class="currency">R$</span>
                            <span class="amount">${productPrice.toFixed(2)}</span>
                            <span class="period">/${durationDays} dias</span>
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
                    <button class="plan-button" onclick="selectPlan(${productId}, ${productPrice}, '${productName}', ${durationDays})" data-product-id="${productId}">
                        ESCOLHER PLANO
                    </button>
                </div>
            `;
        }).join('');

        console.log('✅ Produtos renderizados com sucesso');
    }

    // ===== COMPRA =====
    window.selectPlan = function(productId, productPrice, planName, durationDays) {
        console.log('🔄 Iniciando processo de pagamento...');
        console.log('📦 Product ID:', productId);
        console.log('💰 Preço:', productPrice);
        console.log('📋 Plano:', planName);

        if (!isAuthenticated) {
            showToast('Faça login para comprar', 'warning');
            setTimeout(() => window.location.href = '/login', 1000);
            return;
        }

        // Processar pagamento diretamente
        processPurchase(productId, productPrice, planName, durationDays);
    };

    async function processPurchase(productId, productPrice, planName, durationDays) {

        // Verificar se productId é válido
        if (!productId || productId === 'undefined' || productId === undefined) {
            console.error('❌ Product ID inválido:', productId);
            showToast('Erro: Produto inválido', 'error');
            return;
        }

        try {
            // Converter productId para número se for string
            const numericProductId = parseInt(productId);
            if (isNaN(numericProductId)) {
                console.error('❌ Product ID não é um número válido:', productId);
                showToast('Erro: ID do produto inválido', 'error');
                return;
            }

            console.log('📤 Enviando requisição de checkout...');

            const requestBody = {
                product_id: numericProductId,
                plano: planName || 'Plano Padrão'
            };

            console.log('📄 Body da requisição:', requestBody);

            const response = await fetch('/api/criar-checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(requestBody)
            });

            console.log('📊 Status da resposta:', response.status);

            if (!response.ok) {
                const errorData = await response.json();
                console.error('❌ Erro na resposta:', errorData);
                showToast(errorData.detail || 'Erro ao criar checkout', 'error');
                return;
            }

            // Verificar se a resposta é realmente JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const htmlResponse = await response.text();
                console.error('❌ Resposta não é JSON:', htmlResponse.substring(0, 200));
                showToast('Erro: Resposta inválida do servidor', 'error');
                return;
            }

            const data = await response.json();
            console.log('✅ Dados do checkout recebidos:', data);

            if (data.success && data.init_point) {
                console.log('✅ Redirecionando para pagamento...');
                showToast('Redirecionando para pagamento...', 'info');
                window.location.href = data.init_point;
            } else {
                console.error('❌ Resposta inválida:', data);
                showToast(data.detail || 'Erro ao processar pagamento', 'error');
            }

        } catch (error) {
            console.error('💥 Erro crítico:', error);
            showToast('Erro de conexão com o servidor', 'error');
        }
    }

    // Função para processar compra
    async function buyProduct(productId) {
        // Implementar lógica de compra aqui
        console.log(`Produto ${productId} comprado!`);
    }

    // ===== UTILITÁRIOS =====
    function redirectUser() {
        console.log('🧭 Redirecionando usuário...');
        console.log('👤 Usuário atual:', currentUser?.email);
        console.log('👑 É admin:', currentUser?.is_admin);

        // Forçar atualização da navegação antes de redirecionar
        updateNavigation(true);

        if (currentUser?.is_admin) {
            console.log('🚀 Redirecionando admin para /admin');
            window.location.href = '/admin';
        } else {
            console.log('🚀 Redirecionando usuário para /painel');
            window.location.href = '/painel';
        }
    }

    function setLoading(button, loading) {
        if (!button) return;

        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || button.innerHTML;
        }
    }

    function showToast(message, type = 'info') {
        // Remover toast anterior
        const existingToast = document.querySelector('.toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 'info-circle';

        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;

        // Estilos
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'success' ? '#00ff88' : type === 'error' ? '#ff4444' : '#00d4ff',
            color: '#000',
            padding: '1rem 1.5rem',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            zIndex: '9999',
            fontWeight: '500',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            animation: 'slideIn 0.3s ease-out'
        });

        // Adicionar animação CSS se não existir
        if (!document.querySelector('#toast-animation')) {
            const style = document.createElement('style');
            style.id = 'toast-animation';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) toast.remove();
        }, 5000);
    }

    // Função para limpar completamente a sessão
    function clearSession() {
        // Remover todos os tokens possíveis
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        sessionStorage.removeItem('user_data');

        // Limpar cookies relacionados à autenticação
        document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        });

        console.log('🧹 Sessão completamente limpa');
    }

    // Função para fazer logout
    function logout() {
        console.log('🚪 Fazendo logout...');
        clearSession();

        // Forçar recarregamento completo da página
        window.location.replace('/login');
    }

    // Função para verificar se o usuário está logado
    function isLoggedIn() {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
        const isValid = token !== null && token !== 'undefined' && token !== '';
        console.log('🔍 Verificando login:', isValid ? 'Logado' : 'Não logado');
        return isValid;
    }

    // Função para obter o token
    function getToken() {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
        console.log('🔑 Token obtido:', token ? 'Token presente' : 'Sem token');
        return token;
    }

    // Função para salvar token
    function saveToken(token, rememberMe = false) {
        console.log('💾 Salvando token...');

        // Limpar sessão anterior primeiro
        clearSession();

        // Salvar novo token
        if (rememberMe) {
            localStorage.setItem('access_token', token);
            console.log('💾 Token salvo no localStorage');
        } else {
            sessionStorage.setItem('access_token', token);
            console.log('💾 Token salvo no sessionStorage');
        }
    }

    // Função para fazer requisições autenticadas
    async function authenticatedFetch(url, options = {}) {
        const token = getToken();
        if (!token) {
            console.log('❌ Sem token - redirecionando para login');
            window.location.replace('/login');
            return;
        }

        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                console.log('🚫 Token inválido - fazendo logout');
                logout();
                return;
            }

            return response;
        } catch (error) {
            console.error('❌ Erro na requisição autenticada:', error);
            throw error;
        }
    }

    // Função para validar token no servidor
    async function validateToken() {
        const token = getToken();
        if (!token) {
            return false;
        }

        try {
            const response = await fetch('/api/license/check', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                console.log('🚫 Token inválido no servidor');
                logout();
                return false;
            }

            return response.ok;
        } catch (error) {
            console.error('❌ Erro ao validar token:', error);
            return false;
        }
    }

    // Função para verificar se MercadoPago está disponível
    function isMercadoPagoAvailable() {
        return typeof MercadoPago !== 'undefined' && window.mercadoPagoInstance;
    }

    // ===== FAQ FUNCTIONALITY =====
    function toggleFaq(element) {
        const faqItem = element.closest('.faq-item');
        const faqAnswer = faqItem.querySelector('.faq-answer');
        const isActive = faqItem.classList.contains('active');

        // Fechar todos os outros FAQs
        document.querySelectorAll('.faq-item').forEach(item => {
            if (item !== faqItem) {
                item.classList.remove('active');
                const answer = item.querySelector('.faq-answer');
                if (answer) {
                    answer.style.maxHeight = '0';
                }
            }
        });

        // Toggle do FAQ atual
        if (isActive) {
            faqItem.classList.remove('active');
            faqAnswer.style.maxHeight = '0';
        } else {
            faqItem.classList.add('active');
            faqAnswer.style.maxHeight = faqAnswer.scrollHeight + 'px';
        }
    }

    // ===== FUNÇÕES GLOBAIS EXPOSTAS =====
    window.checkAuthentication = checkAuthentication;
    window.handleLogout = handleLogout;
    window.showToast = showToast;
    window.logout = logout; // Expose the new logout function
    window.isLoggedIn = isLoggedIn; // Expose the new isLoggedIn function
    window.getToken = getToken; // Expose the new getToken function
    window.saveToken = saveToken; // Expose the new saveToken function
    window.authenticatedFetch = authenticatedFetch; // Expose the new authenticatedFetch function
    window.validateToken = validateToken; // Expose the new validateToken function
    window.toggleFaq = toggleFaq; // Expose the FAQ toggle function

})();

// Inicialização quando DOM carrega
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando FovDark...');
    console.log('✅ DOM carregado');

    // Inicializar de forma assíncrona
    initializeApp();
    console.log('🎯 Sistema inicializado com sucesso');
});

// Função de inicialização assíncrona
async function initializeApp() {
    try {
        await checkAuthentication();
    } catch (error) {
        console.error('Erro na inicialização:', error);
    }
}

function handleSuccessfulLogin(data) {
        console.log('✅ Login bem-sucedido para:', data.user.email);

        // Salvar dados do usuário
        const userData = {
            email: data.user.email,
            is_admin: data.user.is_admin
        };

        localStorage.setItem('user_data', JSON.stringify(userData));
        console.log('💾 Dados salvos no localStorage:', userData);

        // Atualizar variáveis globais
        currentUser = userData;
        isAuthenticated = true;

        showToast('Login realizado com sucesso!', 'success');

        console.log('🧭 Redirecionando usuário...');
        console.log('👤 Usuário atual:', currentUser.email);
        console.log('👑 É admin:', currentUser?.is_admin);

        // Forçar atualização da navegação antes de redirecionar
        updateNavigation(true);

        // Aguardar um momento antes de redirecionar para garantir que os dados sejam salvos
        setTimeout(() => {
            if (currentUser?.is_admin) {
                console.log('🚀 Redirecionando admin para /admin');
                window.location.replace('/admin');
            } else {
                console.log('🚀 Redirecionando usuário para /painel');
                window.location.replace('/painel');
            }
        }, 100);
    }