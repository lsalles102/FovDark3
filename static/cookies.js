
// ===== COOKIE UTILITIES =====
class CookieManager {
    constructor() {
        this.preferences = this.loadPreferences();
        this.initializePreferences();
    }

    // Definir cookie
    setCookie(name, value, days = 365) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }

    // Obter cookie
    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    // Deletar cookie
    deleteCookie(name) {
        document.cookie = `${name}=; Max-Age=-99999999; path=/`;
    }

    // Carregar todas as preferências dos cookies
    loadPreferences() {
        const preferences = {
            theme: this.getCookie('fovdark_theme') || 'dark',
            language: this.getCookie('fovdark_language') || 'pt-BR',
            animationsEnabled: this.getCookie('fovdark_animations') !== 'false',
            soundEnabled: this.getCookie('fovdark_sound') !== 'false',
            autoSave: this.getCookie('fovdark_autosave') !== 'false',
            compactMode: this.getCookie('fovdark_compact') === 'true',
            rememberLogin: this.getCookie('fovdark_remember_login') !== 'false',
            showTutorial: this.getCookie('fovdark_show_tutorial') !== 'false',
            dashboardLayout: this.getCookie('fovdark_dashboard_layout') || 'grid',
            fontSize: this.getCookie('fovdark_font_size') || 'medium',
            notificationsEnabled: this.getCookie('fovdark_notifications') !== 'false'
        };

        console.log('🍪 Preferências carregadas dos cookies:', preferences);
        return preferences;
    }

    // Salvar preferência específica
    setPreference(key, value) {
        this.preferences[key] = value;
        this.setCookie(`fovdark_${key}`, value);
        this.applyPreference(key, value);
        console.log(`🍪 Preferência salva: ${key} = ${value}`);
    }

    // Obter preferência específica
    getPreference(key) {
        return this.preferences[key];
    }

    // Aplicar todas as preferências carregadas
    initializePreferences() {
        Object.entries(this.preferences).forEach(([key, value]) => {
            this.applyPreference(key, value);
        });
    }

    // Aplicar preferência específica
    applyPreference(key, value) {
        const root = document.documentElement;

        switch (key) {
            case 'theme':
                this.applyTheme(value);
                break;

            case 'language':
                this.applyLanguage(value);
                break;

            case 'animationsEnabled':
                root.classList.toggle('no-animations', !value);
                break;

            case 'compactMode':
                root.classList.toggle('compact-mode', value);
                break;

            case 'fontSize':
                root.classList.remove('font-small', 'font-medium', 'font-large');
                root.classList.add(`font-${value}`);
                break;

            case 'dashboardLayout':
                const dashboard = document.querySelector('.dashboard-grid');
                if (dashboard) {
                    dashboard.classList.remove('layout-grid', 'layout-list');
                    dashboard.classList.add(`layout-${value}`);
                }
                break;

            case 'soundEnabled':
                // Aplicar configuração de som
                if (window.audioManager) {
                    window.audioManager.setEnabled(value);
                }
                break;
        }
    }

    // Aplicar tema
    applyTheme(theme) {
        const root = document.documentElement;
        root.classList.remove('theme-dark', 'theme-light', 'theme-auto');
        
        if (theme === 'auto') {
            const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            root.classList.add(isDark ? 'theme-dark' : 'theme-light');
        } else {
            root.classList.add(`theme-${theme}`);
        }
    }

    // Aplicar idioma
    applyLanguage(language) {
        document.documentElement.lang = language;
        // Aqui você pode implementar lógica de tradução
    }

    // Resetar todas as preferências
    resetPreferences() {
        const keys = Object.keys(this.preferences);
        keys.forEach(key => {
            this.deleteCookie(`fovdark_${key}`);
        });
        
        // Recarregar preferências padrão
        this.preferences = this.loadPreferences();
        this.initializePreferences();
        
        console.log('🍪 Preferências resetadas');
        showToast('Preferências resetadas para padrão', 'success');
    }

    // Exportar preferências
    exportPreferences() {
        const data = JSON.stringify(this.preferences, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'fovdark_preferences.json';
        a.click();
        
        URL.revokeObjectURL(url);
        console.log('🍪 Preferências exportadas');
    }

    // Importar preferências
    importPreferences(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const importedPrefs = JSON.parse(e.target.result);
                
                // Validar e aplicar preferências importadas
                Object.entries(importedPrefs).forEach(([key, value]) => {
                    if (key in this.preferences) {
                        this.setPreference(key, value);
                    }
                });
                
                showToast('Preferências importadas com sucesso', 'success');
                console.log('🍪 Preferências importadas:', importedPrefs);
            } catch (error) {
                showToast('Erro ao importar preferências', 'error');
                console.error('❌ Erro ao importar preferências:', error);
            }
        };
        reader.readAsText(file);
    }

    // Verificar consentimento para cookies
    checkCookieConsent() {
        const consent = this.getCookie('fovdark_cookie_consent');
        console.log('🍪 Status do consentimento:', consent || 'não definido');
        
        if (!consent || consent === 'undefined') {
            // Aguardar um pouco para garantir que a página carregou
            setTimeout(() => {
                this.showCookieConsent();
                // Bloquear scroll enquanto banner estiver ativo
                document.body.style.overflow = 'hidden';
            }, 1000);
            return false;
        }
        
        return consent === 'accepted' || consent === 'essential';
    }

    // Mostrar banner de consentimento
    showCookieConsent() {
        // Remover qualquer banner existente
        const existingBanner = document.querySelector('.cookie-consent-banner');
        if (existingBanner) {
            existingBanner.remove();
        }

        const banner = document.createElement('div');
        banner.className = 'cookie-consent-banner';
        banner.innerHTML = `
            <div class="cookie-consent-overlay"></div>
            <div class="cookie-consent-content">
                <div class="cookie-consent-text">
                    <h4><i class="fas fa-cookie-bite"></i> 🍪 Política de Cookies</h4>
                    <p><strong>Este site utiliza cookies essenciais para seu funcionamento.</strong></p>
                    <p>Utilizamos cookies para melhorar sua experiência de navegação, personalizar conteúdo, 
                    salvar suas preferências e analisar nosso tráfego. Alguns cookies são necessários 
                    para o funcionamento básico do site.</p>
                    <p>Ao continuar navegando, você concorda com nosso uso de cookies conforme nossa 
                    <a href="/privacy" target="_blank" class="privacy-link">Política de Privacidade</a>.</p>
                </div>
                <div class="cookie-consent-actions">
                    <button class="btn-consent-accept" onclick="cookieManager.acceptCookies()">
                        <i class="fas fa-check"></i> Aceitar Todos os Cookies
                    </button>
                    <button class="btn-consent-essential" onclick="cookieManager.acceptEssentialOnly()">
                        <i class="fas fa-shield-alt"></i> Apenas Essenciais
                    </button>
                    <button class="btn-consent-config" onclick="cookieManager.showCookieSettings()">
                        <i class="fas fa-cog"></i> Configurar
                    </button>
                </div>
            </div>
        `;

        // Adicionar estilos
        const style = document.createElement('style');
        style.textContent = `
            .cookie-consent-banner {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 99999;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.5s ease;
            }
            
            .cookie-consent-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(5px);
            }
            
            .cookie-consent-content {
                position: relative;
                z-index: 100000;
                background: hsl(var(--bg-secondary));
                border: 2px solid hsl(var(--primary));
                border-radius: var(--radius-xl);
                padding: 2rem;
                max-width: 600px;
                width: 90%;
                box-shadow: 
                    0 20px 60px rgba(0, 0, 0, 0.5),
                    0 0 0 1px hsl(var(--primary) / 0.3),
                    inset 0 0 0 1px hsl(var(--primary) / 0.2);
                animation: slideInScale 0.5s ease;
            }
            
            .cookie-consent-text {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .cookie-consent-text h4 {
                margin: 0 0 1rem 0;
                color: hsl(var(--primary));
                font-size: 1.5rem;
                font-family: var(--font-primary);
                text-transform: uppercase;
                letter-spacing: 1px;
                text-shadow: 0 0 10px hsl(var(--primary) / 0.5);
            }
            
            .cookie-consent-text p {
                margin: 0 0 1rem 0;
                color: hsl(var(--text-secondary));
                font-size: 0.95rem;
                line-height: 1.6;
            }
            
            .cookie-consent-text p:last-child {
                margin-bottom: 0;
            }
            
            .privacy-link {
                color: hsl(var(--secondary));
                text-decoration: none;
                font-weight: 600;
                transition: color 0.3s ease;
            }
            
            .privacy-link:hover {
                color: hsl(var(--primary));
                text-shadow: 0 0 5px hsl(var(--primary));
            }
            
            .cookie-consent-actions {
                display: flex;
                gap: 1rem;
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .cookie-consent-actions button {
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: var(--radius-md);
                cursor: pointer;
                font-weight: 700;
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                transition: all 0.3s ease;
                font-family: var(--font-primary);
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .btn-consent-accept {
                background: linear-gradient(135deg, hsl(var(--primary)), hsl(var(--secondary)));
                color: white;
                box-shadow: 0 4px 15px hsl(var(--primary) / 0.4);
            }
            
            .btn-consent-accept:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px hsl(var(--primary) / 0.6);
            }
            
            .btn-consent-essential {
                background: linear-gradient(135deg, hsl(var(--warning)), hsl(var(--warning) / 0.8));
                color: white;
                box-shadow: 0 4px 15px hsl(var(--warning) / 0.4);
            }
            
            .btn-consent-essential:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px hsl(var(--warning) / 0.6);
            }
            
            .btn-consent-config {
                background: transparent;
                color: hsl(var(--text-secondary));
                border: 2px solid hsl(var(--border-primary));
            }
            
            .btn-consent-config:hover {
                background: hsl(var(--bg-tertiary));
                border-color: hsl(var(--primary));
                color: hsl(var(--primary));
                transform: translateY(-2px);
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideInScale {
                from { 
                    opacity: 0;
                    transform: scale(0.8) translateY(50px);
                }
                to { 
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }
            }
            
            @keyframes slideOutDown {
                from { 
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }
                to { 
                    opacity: 0;
                    transform: scale(0.8) translateY(50px);
                }
            }
            
            @media (max-width: 768px) {
                .cookie-consent-content {
                    width: 95%;
                    padding: 1.5rem;
                }
                
                .cookie-consent-text h4 {
                    font-size: 1.25rem;
                }
                
                .cookie-consent-text p {
                    font-size: 0.875rem;
                }
                
                .cookie-consent-actions {
                    flex-direction: column;
                    gap: 0.75rem;
                }
                
                .cookie-consent-actions button {
                    width: 100%;
                    justify-content: center;
                }
            }
        `;
        
        if (document.head) {
            document.head.appendChild(style);
        }
        if (document.body) {
            document.body.appendChild(banner);
        }
    }

    // Aceitar todos os cookies
    acceptCookies() {
        this.setCookie('fovdark_cookie_consent', 'accepted', 365);
        this.removeCookieBanner();
        console.log('🍪 Todos os cookies aceitos pelo usuário');
        if (window.showToast) {
            showToast('Todos os cookies foram aceitos', 'success');
        }
    }

    // Aceitar apenas cookies essenciais
    acceptEssentialOnly() {
        this.setCookie('fovdark_cookie_consent', 'essential', 365);
        // Limpar cookies não essenciais
        const nonEssentialKeys = ['fovdark_animations', 'fovdark_sound', 'fovdark_dashboard_layout'];
        nonEssentialKeys.forEach(key => {
            this.deleteCookie(key);
        });
        this.removeCookieBanner();
        console.log('🍪 Apenas cookies essenciais aceitos pelo usuário');
        if (window.showToast) {
            showToast('Apenas cookies essenciais foram aceitos', 'info');
        }
    }

    // Recusar cookies não essenciais
    declineCookies() {
        this.setCookie('fovdark_cookie_consent', 'declined', 365);
        this.removeCookieBanner();
        // Limpar cookies existentes (exceto consentimento)
        Object.keys(this.preferences).forEach(key => {
            this.deleteCookie(`fovdark_${key}`);
        });
        console.log('🍪 Cookies recusados pelo usuário');
        if (window.showToast) {
            showToast('Cookies não essenciais foram recusados', 'warning');
        }
    }

    // Remover banner
    removeCookieBanner() {
        const banner = document.querySelector('.cookie-consent-banner');
        if (banner) {
            banner.style.animation = 'slideOutDown 0.5s ease';
            setTimeout(() => {
                banner.remove();
                // Restaurar scroll da página
                document.body.style.overflow = '';
            }, 500);
        }
    }

    // Mostrar configurações de cookies
    showCookieSettings() {
        this.removeCookieBanner();
        
        // Abrir modal de preferências se disponível
        if (window.preferencesManager && window.preferencesManager.openModal) {
            window.preferencesManager.openModal();
        } else {
            // Fallback: aceitar cookies essenciais
            if (window.showToast) {
                showToast('Abrindo configurações de preferências...', 'info');
            }
            setTimeout(() => {
                this.acceptEssentialOnly();
            }, 1000);
        }
    }
}

// Inicializar gerenciador de cookies quando DOM estiver pronto
function initializeCookieManager() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.cookieManager = new CookieManager();
            window.cookieManager.checkCookieConsent();
        });
    } else {
        window.cookieManager = new CookieManager();
        window.cookieManager.checkCookieConsent();
    }
}

initializeCookieManager();

console.log('🍪 Sistema de cookies carregado com sucesso');
