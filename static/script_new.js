// ===== SISTEMA DE AUTENTICAÇÃO DARKFOV =====
(function() {
    'use strict';
    
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
                        localStorage.setItem('user_data', JSON.stringify(data.user));
                        currentUser = data.user;
                        isAuthenticated = true;
                        updateNavigation(true);
                        console.log('✅ Usuário autenticado:', currentUser.email);
                        return true;
                    }
                }

                console.log('❌ Resposta inválida do servidor');
                clearAuthData();
                updateNavigation(false);
                return false;

            } catch (networkError) {
                console.error('❌ Erro de rede na verificação:', networkError);
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
            if (loginBtn) loginBtn.style.display = 'none';
            if (registerBtn) registerBtn.style.display = 'none';
            addAuthenticatedButtons(navMenu);
        } else {
            if (loginBtn) loginBtn.style.display = 'flex';
            if (registerBtn) registerBtn.style.display = 'flex';
            removeAuthenticatedButtons();
        }
    }

    function addAuthenticatedButtons(navMenu) {
        if (!navMenu) return;

        removeAuthenticatedButtons();

        const painelBtn = document.createElement('a');
        painelBtn.href = '/painel';
        painelBtn.className = 'nav-link painel-btn';
        painelBtn.innerHTML = '<i class="fas fa-user-circle"></i><span>Painel</span>';
        navMenu.appendChild(painelBtn);

        if (currentUser && currentUser.is_admin) {
            const adminBtn = document.createElement('a');
            adminBtn.href = '/admin';
            adminBtn.className = 'nav-link admin-btn';
            adminBtn.innerHTML = '<i class="fas fa-cog"></i><span>Admin</span>';
            navMenu.appendChild(adminBtn);
        }

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

        const protectedPages = ['/painel', '/admin'];
        if (protectedPages.includes(window.location.pathname)) {
            window.location.href = '/';
        } else {
            checkAuthentication();
        }
    }

    function clearAuthData() {
        console.log('🧹 Limpando dados de autenticação...');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('user_data');
        currentUser = null;
        isAuthenticated = false;
        console.log('✅ Dados limpos');
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
        document.addEventListener('click', function(e) {
            const navLink = e.target.closest('.nav-link');
            const navMenu = document.querySelector('.nav-menu');
            const navToggle = document.querySelector('.nav-toggle');

            if (navLink && navMenu && navToggle) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });

        window.addEventListener('storage', function(e) {
            if (e.key === 'access_token' || e.key === 'user_data') {
                console.log('🔄 Dados de autenticação alterados externamente');
                checkAuthentication();
            }
        });
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
            case '/recover':
                initializeRecoverPage();
                break;
        }
    }

    // ===== LOGIN =====
    function initializeLoginPage() {
        console.log('🔐 Inicializando página de login');

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

            if (!data.access_token || !data.user) {
                throw new Error('Dados de login inválidos recebidos do servidor');
            }

            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_data', JSON.stringify(data.user));

            currentUser = data.user;
            isAuthenticated = true;
            updateNavigation(true);

            showToast('Login realizado com sucesso!', 'success');

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

        if (!email || !password || !confirmPassword) {
            showToast('Preencha todos os campos', 'error');
            return;
        }

        if (password !== confirmPassword) {
            showToast('As senhas não coincidem', 'error');
            return;
        }

        if (password.length < 6) {
            showToast('A senha deve ter pelo menos 6 caracteres', 'error');
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

            if (!response.ok) {
                let errorMessage = 'Erro no registro';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || 'Erro no registro';
                } catch (parseError) {
                    console.error('❌ Erro ao fazer parse da resposta de erro:', parseError);
                }
                showToast(errorMessage, 'error');
                return;
            }

            const data = await response.json();
            showToast('Registro realizado com sucesso! Redirecionando...', 'success');

            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);

        } catch (error) {
            console.error('❌ Erro no registro:', error);
            showToast('Erro de conexão. Tente novamente.', 'error');
        } finally {
            setLoading(submitBtn, false);
        }
    }

    // ===== RECUPERAÇÃO DE SENHA =====
    function initializeRecoverPage() {
        console.log('🔑 Inicializando página de recuperação');

        const recoverForm = document.getElementById('recoverForm');
        const resetForm = document.getElementById('resetForm');

        if (recoverForm) {
            recoverForm.addEventListener('submit', handlePasswordRecovery);
        }

        if (resetForm) {
            resetForm.addEventListener('submit', handlePasswordReset);
        }
    }

    async function handlePasswordRecovery(e) {
        e.preventDefault();

        const form = e.target;
        const email = form.email.value.trim();
        const submitBtn = form.querySelector('button[type="submit"]');

        if (!email) {
            showToast('Digite seu email', 'error');
            return;
        }

        if (!isValidEmail(email)) {
            showToast('Digite um email válido', 'error');
            return;
        }

        setLoading(submitBtn, true);

        try {
            const formData = new FormData();
            formData.append('email', email);

            const response = await fetch('/api/forgot-password', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errorMessage = 'Erro ao enviar email de recuperação';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || 'Erro ao enviar email de recuperação';
                } catch (parseError) {
                    console.error('❌ Erro ao fazer parse da resposta de erro:', parseError);
                }
                showToast(errorMessage, 'error');
                return;
            }

            showToast('Email de recuperação enviado! Verifique sua caixa de entrada.', 'success');
            form.reset();

        } catch (error) {
            console.error('❌ Erro na recuperação:', error);
            showToast('Erro de conexão. Tente novamente.', 'error');
        } finally {
            setLoading(submitBtn, false);
        }
    }

    async function handlePasswordReset(e) {
        e.preventDefault();

        const form = e.target;
        const token = form.token.value.trim();
        const password = form.password.value;
        const confirmPassword = form.confirm_password.value;
        const submitBtn = form.querySelector('button[type="submit"]');

        if (!token || !password || !confirmPassword) {
            showToast('Preencha todos os campos', 'error');
            return;
        }

        if (password !== confirmPassword) {
            showToast('As senhas não coincidem', 'error');
            return;
        }

        if (password.length < 6) {
            showToast('A senha deve ter pelo menos 6 caracteres', 'error');
            return;
        }

        setLoading(submitBtn, true);

        try {
            const formData = new FormData();
            formData.append('token', token);
            formData.append('password', password);
            formData.append('confirm_password', confirmPassword);

            const response = await fetch('/api/reset-password', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errorMessage = 'Erro ao redefinir senha';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || 'Erro ao redefinir senha';
                } catch (parseError) {
                    console.error('❌ Erro ao fazer parse da resposta de erro:', parseError);
                }
                showToast(errorMessage, 'error');
                return;
            }

            showToast('Senha redefinida com sucesso! Redirecionando para login...', 'success');

            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);

        } catch (error) {
            console.error('❌ Erro ao redefinir senha:', error);
            showToast('Erro de conexão. Tente novamente.', 'error');
        } finally {
            setLoading(submitBtn, false);
        }
    }

    // ===== PAINEL =====
    function initializePainelPage() {
        if (!isAuthenticated) {
            console.log('❌ Usuário não autenticado, redirecionando...');
            window.location.href = '/login';
            return;
        }

        const changePasswordForm = document.getElementById('changePasswordForm');
        if (changePasswordForm) {
            changePasswordForm.addEventListener('submit', handleChangePassword);
        }
    }

    async function handleChangePassword(e) {
        e.preventDefault();

        const form = e.target;
        const currentPassword = form.current_password.value;
        const newPassword = form.new_password.value;
        const confirmPassword = form.confirm_password.value;
        const submitBtn = form.querySelector('button[type="submit"]');

        if (!currentPassword || !newPassword || !confirmPassword) {
            showToast('Preencha todos os campos', 'error');
            return;
        }

        if (newPassword !== confirmPassword) {
            showToast('As novas senhas não coincidem', 'error');
            return;
        }

        if (newPassword.length < 6) {
            showToast('A nova senha deve ter pelo menos 6 caracteres', 'error');
            return;
        }

        setLoading(submitBtn, true);

        try {
            const token = localStorage.getItem('access_token');
            const formData = new FormData();
            formData.append('current_password', currentPassword);
            formData.append('new_password', newPassword);

            const response = await fetch('/api/change-password', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                let errorMessage = 'Erro ao alterar senha';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || 'Erro ao alterar senha';
                } catch (parseError) {
                    console.error('❌ Erro ao fazer parse da resposta de erro:', parseError);
                }
                showToast(errorMessage, 'error');
                return;
            }

            showToast('Senha alterada com sucesso!', 'success');
            form.reset();

        } catch (error) {
            console.error('❌ Erro ao alterar senha:', error);
            showToast('Erro de conexão. Tente novamente.', 'error');
        } finally {
            setLoading(submitBtn, false);
        }
    }

    // ===== ADMIN =====
    function initializeAdminPage() {
        if (!isAuthenticated || !currentUser?.is_admin) {
            console.log('❌ Acesso negado, redirecionando...');
            window.location.href = '/';
            return;
        }
        console.log('👨‍💼 Página admin inicializada');
    }

    // ===== UTILITÁRIOS =====
    function redirectUser() {
        if (currentUser?.is_admin) {
            window.location.href = '/admin';
        } else {
            window.location.href = '/painel';
        }
    }

    function setLoading(button, loading) {
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

    function showToast(message, type = 'info') {
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }, 4000);
    }

    function getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'times-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // ===== FUNÇÕES GLOBAIS EXPOSTAS =====
    window.checkAuthentication = checkAuthentication;
    window.handleLogout = handleLogout;
    window.showToast = showToast;

})();