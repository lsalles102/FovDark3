
// ===== USER PREFERENCES INTERFACE =====
class PreferencesManager {
    constructor() {
        this.modal = null;
        this.createPreferencesModal();
    }

    // Criar modal de preferências
    createPreferencesModal() {
        const modal = document.createElement('div');
        modal.className = 'preferences-modal';
        modal.style.display = 'none';
        
        modal.innerHTML = `
            <div class="preferences-overlay" onclick="preferencesManager.closeModal()"></div>
            <div class="preferences-content">
                <div class="preferences-header">
                    <h2><i class="fas fa-cog"></i> Preferências do Usuário</h2>
                    <button class="btn-close" onclick="preferencesManager.closeModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="preferences-body">
                    <div class="preferences-tabs">
                        <button class="tab-btn active" data-tab="appearance">
                            <i class="fas fa-palette"></i> Aparência
                        </button>
                        <button class="tab-btn" data-tab="behavior">
                            <i class="fas fa-mouse-pointer"></i> Comportamento
                        </button>
                        <button class="tab-btn" data-tab="privacy">
                            <i class="fas fa-shield-alt"></i> Privacidade
                        </button>
                        <button class="tab-btn" data-tab="advanced">
                            <i class="fas fa-tools"></i> Avançado
                        </button>
                    </div>
                    
                    <div class="preferences-panels">
                        <!-- Aparência -->
                        <div class="preference-panel active" data-panel="appearance">
                            <div class="preference-group">
                                <h3>Tema</h3>
                                <div class="preference-item">
                                    <label>Modo de cores</label>
                                    <select id="theme-select">
                                        <option value="dark">Escuro</option>
                                        <option value="light">Claro</option>
                                        <option value="auto">Automático</option>
                                    </select>
                                </div>
                                
                                <div class="preference-item">
                                    <label>Tamanho da fonte</label>
                                    <select id="font-size-select">
                                        <option value="small">Pequena</option>
                                        <option value="medium">Média</option>
                                        <option value="large">Grande</option>
                                    </select>
                                </div>
                                
                                <div class="preference-item">
                                    <label>Modo compacto</label>
                                    <input type="checkbox" id="compact-mode">
                                    <span class="toggle-slider"></span>
                                </div>
                            </div>
                            
                            <div class="preference-group">
                                <h3>Layout do Dashboard</h3>
                                <div class="preference-item">
                                    <label>Visualização</label>
                                    <select id="dashboard-layout-select">
                                        <option value="grid">Grade</option>
                                        <option value="list">Lista</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Comportamento -->
                        <div class="preference-panel" data-panel="behavior">
                            <div class="preference-group">
                                <h3>Animações</h3>
                                <div class="preference-item">
                                    <label>Ativar animações</label>
                                    <input type="checkbox" id="animations-enabled">
                                    <span class="toggle-slider"></span>
                                </div>
                                
                                <div class="preference-item">
                                    <label>Sons do sistema</label>
                                    <input type="checkbox" id="sound-enabled">
                                    <span class="toggle-slider"></span>
                                </div>
                            </div>
                            
                            <div class="preference-group">
                                <h3>Salvamento</h3>
                                <div class="preference-item">
                                    <label>Salvamento automático</label>
                                    <input type="checkbox" id="auto-save">
                                    <span class="toggle-slider"></span>
                                </div>
                                
                                <div class="preference-item">
                                    <label>Lembrar login</label>
                                    <input type="checkbox" id="remember-login">
                                    <span class="toggle-slider"></span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Privacidade -->
                        <div class="preference-panel" data-panel="privacy">
                            <div class="preference-group">
                                <h3>Cookies e Dados</h3>
                                <div class="preference-item">
                                    <label>Notificações</label>
                                    <input type="checkbox" id="notifications-enabled">
                                    <span class="toggle-slider"></span>
                                </div>
                                
                                <div class="preference-item">
                                    <label>Tutorial para novos usuários</label>
                                    <input type="checkbox" id="show-tutorial">
                                    <span class="toggle-slider"></span>
                                </div>
                            </div>
                            
                            <div class="preference-group">
                                <h3>Gerenciar Dados</h3>
                                <div class="preference-actions">
                                    <button class="btn-action" onclick="cookieManager.exportPreferences()">
                                        <i class="fas fa-download"></i> Exportar Preferências
                                    </button>
                                    <label class="btn-action file-input-label">
                                        <i class="fas fa-upload"></i> Importar Preferências
                                        <input type="file" id="import-preferences" accept=".json" onchange="preferencesManager.handleImport(this)">
                                    </label>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Avançado -->
                        <div class="preference-panel" data-panel="advanced">
                            <div class="preference-group">
                                <h3>Idioma</h3>
                                <div class="preference-item">
                                    <label>Idioma do sistema</label>
                                    <select id="language-select">
                                        <option value="pt-BR">Português (Brasil)</option>
                                        <option value="en-US">English (US)</option>
                                        <option value="es-ES">Español</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="preference-group">
                                <h3>Reset</h3>
                                <div class="preference-actions">
                                    <button class="btn-danger" onclick="preferencesManager.resetAllPreferences()">
                                        <i class="fas fa-undo"></i> Resetar Todas as Preferências
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="preferences-footer">
                    <button class="btn-secondary" onclick="preferencesManager.closeModal()">
                        <i class="fas fa-times"></i> Cancelar
                    </button>
                    <button class="btn-primary" onclick="preferencesManager.savePreferences()">
                        <i class="fas fa-save"></i> Salvar Preferências
                    </button>
                </div>
            </div>
        `;
        
        if (document.body) {
            document.body.appendChild(modal);
        }
        this.modal = modal;
        this.setupEventListeners();
        this.addStyles();
    }

    // Adicionar estilos do modal
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .preferences-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .preferences-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
                backdrop-filter: blur(5px);
            }
            
            .preferences-content {
                position: relative;
                background: var(--background-dark);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                width: 90%;
                max-width: 800px;
                max-height: 90vh;
                overflow: hidden;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                animation: modalSlideIn 0.3s ease;
            }
            
            .preferences-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 20px;
                border-bottom: 1px solid var(--border-color);
                background: var(--background-darker);
            }
            
            .preferences-header h2 {
                margin: 0;
                color: var(--primary);
                font-size: 1.4rem;
            }
            
            .btn-close {
                background: none;
                border: none;
                color: var(--text-secondary);
                font-size: 1.2rem;
                cursor: pointer;
                padding: 5px;
                border-radius: 4px;
                transition: all 0.3s ease;
            }
            
            .btn-close:hover {
                background: var(--danger);
                color: white;
            }
            
            .preferences-body {
                display: flex;
                min-height: 400px;
            }
            
            .preferences-tabs {
                display: flex;
                flex-direction: column;
                background: var(--background-darker);
                min-width: 200px;
                border-right: 1px solid var(--border-color);
            }
            
            .tab-btn {
                background: none;
                border: none;
                padding: 15px 20px;
                text-align: left;
                color: var(--text-secondary);
                cursor: pointer;
                transition: all 0.3s ease;
                border-bottom: 1px solid var(--border-color);
            }
            
            .tab-btn:hover {
                background: var(--background-dark);
                color: var(--text);
            }
            
            .tab-btn.active {
                background: var(--primary);
                color: white;
            }
            
            .preferences-panels {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }
            
            .preference-panel {
                display: none;
            }
            
            .preference-panel.active {
                display: block;
            }
            
            .preference-group {
                margin-bottom: 30px;
            }
            
            .preference-group h3 {
                margin: 0 0 15px 0;
                color: var(--primary);
                font-size: 1.1rem;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 5px;
            }
            
            .preference-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .preference-item:last-child {
                border-bottom: none;
            }
            
            .preference-item label {
                color: var(--text);
                font-weight: 500;
            }
            
            .preference-item select {
                background: var(--background-darker);
                border: 1px solid var(--border-color);
                color: var(--text);
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 150px;
            }
            
            .preference-item input[type="checkbox"] {
                display: none;
            }
            
            .toggle-slider {
                position: relative;
                width: 50px;
                height: 25px;
                background: var(--background-darker);
                border-radius: 25px;
                cursor: pointer;
                transition: all 0.3s ease;
                border: 1px solid var(--border-color);
            }
            
            .toggle-slider:before {
                content: '';
                position: absolute;
                width: 19px;
                height: 19px;
                border-radius: 50%;
                background: var(--text-secondary);
                top: 2px;
                left: 3px;
                transition: all 0.3s ease;
            }
            
            input[type="checkbox"]:checked + .toggle-slider {
                background: var(--primary);
            }
            
            input[type="checkbox"]:checked + .toggle-slider:before {
                transform: translateX(24px);
                background: white;
            }
            
            .preference-actions {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            .btn-action, .file-input-label {
                background: var(--secondary);
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s ease;
            }
            
            .btn-action:hover, .file-input-label:hover {
                background: var(--secondary-dark);
            }
            
            .btn-danger {
                background: var(--danger);
            }
            
            .btn-danger:hover {
                background: #c53030;
            }
            
            .file-input-label input {
                display: none;
            }
            
            .preferences-footer {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                padding: 20px;
                border-top: 1px solid var(--border-color);
                background: var(--background-darker);
            }
            
            .btn-primary, .btn-secondary {
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s ease;
            }
            
            .btn-primary {
                background: var(--primary);
                color: white;
            }
            
            .btn-secondary {
                background: transparent;
                color: var(--text-secondary);
                border: 1px solid var(--border-color);
            }
            
            @keyframes modalSlideIn {
                from {
                    opacity: 0;
                    transform: scale(0.9) translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }
            }
            
            @media (max-width: 768px) {
                .preferences-content {
                    width: 95%;
                    height: 90vh;
                }
                
                .preferences-body {
                    flex-direction: column;
                }
                
                .preferences-tabs {
                    flex-direction: row;
                    min-width: auto;
                    overflow-x: auto;
                }
                
                .tab-btn {
                    white-space: nowrap;
                    min-width: 120px;
                }
            }
        `;
        
        if (document.head) {
            document.head.appendChild(style);
        }
    }

    // Configurar event listeners
    setupEventListeners() {
        // Tabs
        this.modal.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Inputs
        this.setupInputListeners();
    }

    // Configurar listeners dos inputs
    setupInputListeners() {
        const inputs = {
            'theme-select': 'theme',
            'font-size-select': 'fontSize',
            'dashboard-layout-select': 'dashboardLayout',
            'language-select': 'language',
            'compact-mode': 'compactMode',
            'animations-enabled': 'animationsEnabled',
            'sound-enabled': 'soundEnabled',
            'auto-save': 'autoSave',
            'remember-login': 'rememberLogin',
            'notifications-enabled': 'notificationsEnabled',
            'show-tutorial': 'showTutorial'
        };

        Object.entries(inputs).forEach(([inputId, prefKey]) => {
            const input = this.modal.querySelector(`#${inputId}`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = cookieManager.getPreference(prefKey);
                    input.addEventListener('change', () => {
                        cookieManager.setPreference(prefKey, input.checked);
                    });
                } else {
                    input.value = cookieManager.getPreference(prefKey);
                    input.addEventListener('change', () => {
                        cookieManager.setPreference(prefKey, input.value);
                    });
                }
            }
        });
    }

    // Trocar aba
    switchTab(tabName) {
        // Remover active de todas as abas
        this.modal.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        this.modal.querySelectorAll('.preference-panel').forEach(panel => {
            panel.classList.remove('active');
        });

        // Ativar aba selecionada
        this.modal.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        this.modal.querySelector(`[data-panel="${tabName}"]`).classList.add('active');
    }

    // Abrir modal
    openModal() {
        this.modal.style.display = 'flex';
        this.setupInputListeners(); // Atualizar valores
        document.body.style.overflow = 'hidden';
    }

    // Fechar modal
    closeModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    // Salvar preferências
    savePreferences() {
        showToast('Preferências salvas com sucesso!', 'success');
        this.closeModal();
    }

    // Resetar todas as preferências
    resetAllPreferences() {
        if (confirm('Tem certeza que deseja resetar todas as preferências? Esta ação não pode ser desfeita.')) {
            cookieManager.resetPreferences();
            this.setupInputListeners(); // Atualizar interface
        }
    }

    // Importar preferências
    handleImport(input) {
        const file = input.files[0];
        if (file) {
            cookieManager.importPreferences(file);
            this.setupInputListeners(); // Atualizar interface
        }
    }
}

// Inicializar gerenciador de preferências quando DOM estiver pronto
function initializePreferencesManager() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.preferencesManager = new PreferencesManager();
        });
    } else {
        window.preferencesManager = new PreferencesManager();
    }
}

initializePreferencesManager();

// Função para abrir preferências
function openPreferences() {
    if (window.preferencesManager) {
        window.preferencesManager.openModal();
    }
}

console.log('⚙️ Sistema de preferências carregado com sucesso');
