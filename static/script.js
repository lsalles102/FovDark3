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

        // Tratar erros específicos do MercadoPago
        if (e.message && e.message.includes('MercadoPago is not defined')) {
            console.log('🔄 Tentando recarregar MercadoPago SDK...');
            if (typeof window.initializeMercadoPago === 'function') {
                window.initializeMercadoPago().then(function() {
                    console.log('✅ MercadoPago recarregado com sucesso');
                }).catch(function(err) {
                    console.error('❌ Falha ao recarregar MercadoPago:', err);
                });
            }
        }

        return true; // Previne que o erro pare a execução
    });

    window.addEventListener('unhandledrejection', function(e) {
        console.error('Promise rejeitada não tratada:', e.reason);

        // Tratar promises rejeitadas do MercadoPago
        if (e.reason && (
            (e.reason.message && e.reason.message.includes('MercadoPago')) ||
            (e.reason.message && e.reason.message.includes('Params Error')) ||
            (e.reason.code && e.reason.code === 'bad_request')
        )) {
            console.log('🔄 Erro do MercadoPago detectado - possivelmente parâmetros inválidos');
            console.log('💡 Sugestão: Verificar se apenas public_key e locale estão sendo enviados');

            // Tentar reinicializar MercadoPago com configuração limpa
            if (typeof window.initializeMercadoPago === 'function') {
                setTimeout(() => {
                    console.log('🔄 Tentando reinicializar MercadoPago...');
                    window.initializeMercadoPago().catch(err => {
                        console.error('❌ Falha na reinicialização:', err);
                    });
                }, 2000);
            }
        }

        // Tratar erros de autenticação
        if (e.reason && e.reason.message && e.reason.message.includes('401')) {
            console.log('🚫 Erro de autenticação detectado - redirecionando para login');
            clearAuthData();
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }

        e.preventDefault(); // Previne que apareça no console como erro não tratado
    });

    // ===== AUTENTICAÇÃO =====
    async function checkAuthentication() {
        try {
            console.log('🔍 Verificando autenticação...');
            const token = localStorage.getItem('access_token');
            const userData = localStorage.getItem('user_data');

            if (!token || token === 'null' || token === 'undefined') {
                console.log('❌ Token não encontrado ou inválido');
                clearAuthData();
                updateNavigation(false);
                return false;
            }

            try {
                // Verificar token no servidor usando endpoint correto
                const response = await fetch('/api/verify_token', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.status === 401) {
                    console.log('❌ Token expirado ou inválido');
                    clearAuthData();
                    updateNavigation(false);
                    return false;
                }

                if (response.ok) {
                    const data = await response.json();
                    if (data.valid && data.user) {
                        // Atualizar dados do usuário
                        localStorage.setItem('user_data', JSON.stringify(data.user));
                        currentUser = data.user;
                        isAuthenticated = true;
                        updateNavigation(true);
                        console.log('✅ Usuário autenticado:', currentUser.email);
                        return true;
                    }
                }

                // Se chegou aqui, token é inválido
                console.log('❌ Resposta inválida do servidor');
                clearAuthData();
                updateNavigation(false);
                return false;

            } catch (networkError) {
                console.error('❌ Erro de rede na verificação:', networkError);

                // Se há dados salvos e é erro de rede, usar temporariamente
                if (userData) {
                    try {
                        const parsedUserData = JSON.parse(userData);
                        currentUser = parsedUserData;
                        isAuthenticated = true;
                        updateNavigation(true);
                        console.log('⚠️ Usando dados salvos (erro de rede):', currentUser.email);
                        return true;
                    } catch (parseError) {
                        console.error('❌ Erro ao fazer parse dos dados salvos:', parseError);
                    }
                }

                clearAuthData();
                updateNavigation(false);
                return false;
            }
        } catch (error) {
            console.error('❌ Erro geral na autenticação:', error);
            clearAuthData();
            updateNavigation(false);
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
            console.log('🔄 Iniciando login...');

            // Limpar dados antigos
            clearAuthData();

            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);

            const response = await fetch('/api/login', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errorMessage = 'Erro no login';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || 'Erro no login';
                } catch (parseError) {
                    console.error('❌ Erro ao fazer parse da resposta de erro:', parseError);
                }
                console.log('❌ Erro no login:', errorMessage);
                showToast(errorMessage, 'error');
                return;
            }

            const data = await response.json();
            console.log('✅ Login bem-sucedido para:', data.user?.email);

            // Validar dados recebidos
            if (!data.access_token || !data.user) {
                throw new Error('Dados de login inválidos recebidos do servidor');
            }

            // Salvar dados
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_data', JSON.stringify(data.user));

            // Atualizar estado
            currentUser = data.user;
            isAuthenticated = true;
            updateNavigation(true);

            showToast('Login realizado com sucesso!', 'success');

            // Redirecionar baseado no tipo de usuário
            setTimeout(() => {
                if (data.user.is_admin) {
                    console.log('🚀 Redirecionando admin para /admin');
                    window.location.replace('/admin');
                } else {
                    console.log('🚀 Redirecionando usuário para /painel');
                    window.location.replace('/painel');
                }
            }, 1000);

        } catch (error) {
            console.error('❌ Erro crítico no login:', error);
            showToast('Erro de conexão. Tente novamente.', 'error');
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

    async function initializeComprarPage() {
        console.log('🛒 Inicializando página de compras');

        // Verificar autenticação primeiro
        const authValid = await checkAuthentication();
        console.log('🔍 Status de autenticação na página de compras:', authValid ? 'Autenticado' : 'Não autenticado');

        // Carregar produtos independentemente do status de autenticação
        loadProducts();

        // Mostrar aviso se não estiver logado
        if (!authValid) {
            console.log('⚠️ Usuário não autenticado - mostrando aviso');
            setTimeout(() => {
                if (typeof showToast === 'function') {
                    showToast('Faça login para realizar compras', 'info');
                }
            }, 2000);
        }
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
                    <button class="plan-button" onclick="chooseCheckoutMethod('${productName}', ${productPrice}, ${durationDays}, ${productId})" data-product-id="${productId}">
                        ESCOLHER PLANO
                    </button>
                </div>
            `;
        }).join('');

        console.log('✅ Produtos renderizados com sucesso');
    }

    // ===== COMPRA =====
    window.selectPlan = function(productId, productPrice, planName, durationDays) {
        console.log('🔄 Iniciando processo de compra...');
        console.log('📦 Product ID:', productId);
        console.log('💰 Preço:', productPrice);
        console.log('📋 Plano:', planName);

        if (!isAuthenticated) {
            showToast('Faça login para comprar', 'warning');
            setTimeout(() => window.location.href = '/login', 1000);
            return;
        }

        // Processar compra diretamente
        processPurchase(productId, productPrice, planName, durationDays);
    };

    // ===== PURCHASE FUNCTIONS =====

// Função para processar compra (sistema simplificado)
async function processPurchase(productId, productPrice, planName, durationDays) {
    console.log('🚀 Iniciando processo de compra...');
    console.log('📦 Dados do produto:', {
        productId,
        productPrice,
        planName,
        durationDays
    });

    // Verificar se productId é válido
    if (!productId || productId === 'undefined' || productId === undefined) {
        console.error('❌ Product ID inválido:', productId);
        if (typeof showToast === 'function') {
            showToast('Erro: Produto inválido', 'error');
        }
        return;
    }

    // Verificar autenticação
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log('❌ Token não encontrado');
        if (typeof showToast === 'function') {
            showToast('Faça login para continuar', 'warning');
        }
        setTimeout(() => window.location.href = '/login', 1000);
        return;
    }

    // Mostrar mensagem informativa
    if (typeof showToast === 'function') {
        showToast('Sistema de pagamento em desenvolvimento. Entre em contato para adquirir a licença.', 'info');
    }
}

    // Função para processar compra
    function buyProduct(productId) {
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
            return```tool_code
 false;
        }try {
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
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Inicializando FovDark...');
    console.log('✅ DOM carregado');

    // Inicializar de forma assíncrona
    await initializeApp();
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

        console.log('🧭 Redirecioncionando usuário...');
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

async function chooseCheckoutMethod(planName, price, durationDays, productId) {
    console.log('🛒 Produto selecionado:', { planName, price, durationDays, productId });

    // Verificar autenticação
    const token = localStorage.getItem('access_token');
    if (!token || token === 'null' || token === 'undefined') {
        console.log('❌ Token não encontrado');
        if (typeof showToast === 'function') {
            showToast('Faça login para comprar', 'warning');
        }
        setTimeout(() => window.location.href = '/login', 1000);
        return;
    }

    // Verificar se o token é válido no servidor
    try {
        console.log('🔍 Validando token no servidor...');
        const response = await fetch('/api/verify_token', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            console.log('❌ Token expirado ou inválido');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_data');
            if (typeof showToast === 'function') {
                showToast('Sessão expirada. Faça login novamente', 'warning');
            }
            setTimeout(() => window.location.href = '/login', 1000);
            return;
        }

        if (!response.ok) {
            throw new Error(`Erro de verificação: ${response.status}`);
        }

        const userData = await response.json();
        if (!userData.valid) {
            console.log('❌ Token inválido segundo servidor');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_data');
            if (typeof showToast === 'function') {
                showToast('Sessão inválida. Faça login novamente', 'warning');
            }
            setTimeout(() => window.location.href = '/login', 1000);
            return;
        }

        console.log('✅ Usuário autenticado:', userData.user.email);

        // Atualizar dados do usuário se necessário
        if (userData.user) {
            localStorage.setItem('user_data', JSON.stringify(userData.user));
            if (typeof currentUser !== 'undefined') {
                currentUser = userData.user;
            }
            if (typeof isAuthenticated !== 'undefined') {
                isAuthenticated = true;
            }
        }

        // Mostrar mensagem sobre sistema de pagamento
        if (typeof showToast === 'function') {
            showToast('Sistema de pagamento em desenvolvimento. Entre em contato para adquirir a licença.', 'info');
        }

    } catch (error) {
        console.error('❌ Erro ao verificar autenticação:', error);
        if (typeof showToast === 'function') {
            showToast('Erro de conexão. Tente novamente.', 'error');
        }
        return;
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

