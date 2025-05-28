
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
        if (!consent) {
            this.showCookieConsent();
        }
        return consent === 'accepted';
    }

    // Mostrar banner de consentimento
    showCookieConsent() {
        const banner = document.createElement('div');
        banner.className = 'cookie-consent-banner';
        banner.innerHTML = `
            <div class="cookie-consent-content">
                <div class="cookie-consent-text">
                    <h4><i class="fas fa-cookie-bite"></i> Uso de Cookies</h4>
                    <p>Utilizamos cookies para melhorar sua experiência de navegação, personalizar conteúdo e analisar nosso tráfego. 
                    Ao continuar navegando, você concorda com nosso uso de cookies.</p>
                </div>
                <div class="cookie-consent-actions">
                    <button class="btn-consent-accept" onclick="cookieManager.acceptCookies()">
                        <i class="fas fa-check"></i> Aceitar Todos
                    </button>
                    <button class="btn-consent-config" onclick="cookieManager.showCookieSettings()">
                        <i class="fas fa-cog"></i> Configurar
                    </button>
                    <button class="btn-consent-decline" onclick="cookieManager.declineCookies()">
                        <i class="fas fa-times"></i> Recusar
                    </button>
                </div>
            </div>
        `;

        // Adicionar estilos
        const style = document.createElement('style');
        style.textContent = `
            .cookie-consent-banner {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: var(--background-darker);
                border-top: 2px solid var(--primary);
                padding: 20px;
                z-index: 10000;
                box-shadow: 0 -4px 20px rgba(0,0,0,0.3);
                animation: slideInUp 0.3s ease;
            }
            
            .cookie-consent-content {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 20px;
                flex-wrap: wrap;
            }
            
            .cookie-consent-text h4 {
                margin: 0 0 8px 0;
                color: var(--primary);
                font-size: 1.1rem;
            }
            
            .cookie-consent-text p {
                margin: 0;
                color: var(--text-secondary);
                font-size: 0.9rem;
                line-height: 1.4;
            }
            
            .cookie-consent-actions {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            .cookie-consent-actions button {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }
            
            .btn-consent-accept {
                background: var(--primary);
                color: white;
            }
            
            .btn-consent-config {
                background: var(--secondary);
                color: white;
            }
            
            .btn-consent-decline {
                background: transparent;
                color: var(--text-secondary);
                border: 1px solid var(--border-color);
            }
            
            @keyframes slideInUp {
                from { transform: translateY(100%); }
                to { transform: translateY(0); }
            }
            
            @media (max-width: 768px) {
                .cookie-consent-content {
                    flex-direction: column;
                    text-align: center;
                }
                
                .cookie-consent-actions {
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

    // Aceitar cookies
    acceptCookies() {
        this.setCookie('fovdark_cookie_consent', 'accepted', 365);
        this.removeCookieBanner();
        showToast('Cookies aceitos', 'success');
    }

    // Recusar cookies
    declineCookies() {
        this.setCookie('fovdark_cookie_consent', 'declined', 365);
        this.removeCookieBanner();
        // Limpar cookies existentes (exceto consentimento)
        Object.keys(this.preferences).forEach(key => {
            this.deleteCookie(`fovdark_${key}`);
        });
        showToast('Cookies recusados', 'info');
    }

    // Remover banner
    removeCookieBanner() {
        const banner = document.querySelector('.cookie-consent-banner');
        if (banner) {
            banner.style.animation = 'slideOutDown 0.3s ease';
            setTimeout(() => banner.remove(), 300);
        }
    }

    // Mostrar configurações de cookies
    showCookieSettings() {
        // Esta função pode abrir um modal com configurações detalhadas
        showToast('Funcionalidade em desenvolvimento', 'info');
        this.acceptCookies(); // Por enquanto, aceita automaticamente
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
