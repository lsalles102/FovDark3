
// ===== MERCADOPAGO INITIALIZATION =====
(function() {
    'use strict';
    
    console.log('🔧 Inicializando módulo MercadoPago...');

    // Estado global do MercadoPago
    window.mercadoPagoState = {
        isLoaded: false,
        isInitialized: false,
        instance: null,
        publicKey: null
    };

    // Função para verificar se MercadoPago está disponível
    window.isMercadoPagoAvailable = function() {
        return window.mercadoPagoState.isLoaded && 
               window.mercadoPagoState.isInitialized && 
               window.mercadoPagoState.instance !== null;
    };

    // Função para obter a instância do MercadoPago
    window.getMercadoPagoInstance = function() {
        return window.mercadoPagoState.instance;
    };

    // Função para inicializar MercadoPago
    window.initializeMercadoPago = function() {
        return new Promise(function(resolve, reject) {
            console.log('🚀 Iniciando inicialização do MercadoPago...');

            // Verificar se já está inicializado
            if (window.mercadoPagoState.isInitialized && window.mercadoPagoState.instance) {
                console.log('✅ MercadoPago já inicializado');
                resolve(window.mercadoPagoState.instance);
                return;
            }

            // Verificar se o SDK está carregado
            if (typeof MercadoPago === 'undefined' || !MercadoPago) {
                console.log('⏳ SDK do MercadoPago não carregado ainda, aguardando...');
                
                // Aguardar até 10 segundos pelo SDK
                var attempts = 0;
                var maxAttempts = 50; // 50 x 200ms = 10 segundos
                
                var checkInterval = setInterval(function() {
                    attempts++;
                    
                    if (typeof MercadoPago !== 'undefined' && MercadoPago) {
                        clearInterval(checkInterval);
                        console.log('✅ SDK do MercadoPago detectado após ' + (attempts * 200) + 'ms');
                        initializeMercadoPagoInstance(resolve, reject);
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkInterval);
                        console.error('❌ Timeout: SDK do MercadoPago não carregou após 10 segundos');
                        reject(new Error('SDK do MercadoPago não carregou - verifique CSP e conectividade'));
                    } else if (attempts % 15 === 0) {
                        console.log('⏳ Ainda aguardando MercadoPago... tentativa ' + attempts + '/' + maxAttempts);
                    }
                }, 200);
            } else {
                // SDK já carregado, inicializar imediatamente
                console.log('✅ SDK do MercadoPago já disponível');
                initializeMercadoPagoInstance(resolve, reject);
            }
        });
    };

    // Função interna para inicializar a instância
    function initializeMercadoPagoInstance(resolve, reject) {
        try {
            console.log('🔧 Criando instância do MercadoPago...');

            // Verificação robusta se MercadoPago está disponível
            if (typeof MercadoPago === 'undefined' || !MercadoPago || typeof MercadoPago !== 'function') {
                console.error('❌ MercadoPago não está disponível no momento da inicialização');
                console.error('❌ Tipo detectado:', typeof MercadoPago);
                console.error('❌ Valor:', MercadoPago);
                reject(new Error('MercadoPago SDK não disponível'));
                return;
            }

            console.log('✅ MercadoPago SDK confirmado como disponível:', typeof MercadoPago);

            // Obter chave pública do backend
            fetch('/api/mercadopago/public-key')
                .then(function(response) {
                    if (!response.ok) {
                        throw new Error('Falha ao obter chave pública: ' + response.status);
                    }
                    return response.json();
                })
                .then(function(data) {
                    if (!data.public_key) {
                        throw new Error('Chave pública não encontrada na resposta');
                    }

                    console.log('🔑 Chave pública obtida:', data.public_key.substring(0, 20) + '...');

                    try {
                        // Criar instância do MercadoPago com configuração mais robusta
                        var mp = new MercadoPago(data.public_key, {
                            locale: 'pt-BR',
                            advancedFraudPrevention: false // Desabilitar para evitar erros de configuração
                        });

                        // Aguardar um momento para garantir que a instância foi criada
                        setTimeout(function() {
                            // Atualizar estado global
                            window.mercadoPagoState.isLoaded = true;
                            window.mercadoPagoState.isInitialized = true;
                            window.mercadoPagoState.instance = mp;
                            window.mercadoPagoState.publicKey = data.public_key;

                            console.log('✅ MercadoPago inicializado com sucesso');
                            console.log('📊 Estado:', window.mercadoPagoState);

                            resolve(mp);
                        }, 100);

                    } catch (mpError) {
                        console.error('❌ Erro ao criar instância MercadoPago:', mpError);
                        throw mpError;
                    }
                })
                .catch(function(error) {
                    console.error('❌ Erro ao obter chave pública:', error);
                    
                    // Tentar com chave de teste como fallback apenas se não for erro de SDK
                    if (typeof MercadoPago !== 'undefined' && MercadoPago) {
                        console.log('🔄 Tentando inicializar com configuração de fallback...');
                        
                        try {
                            var mp = new MercadoPago('TEST-c8c68306-c9a2-4ec8-98db-0b00ad3c6dd9', {
                                locale: 'pt-BR',
                                advancedFraudPrevention: false
                            });

                            setTimeout(function() {
                                window.mercadoPagoState.isLoaded = true;
                                window.mercadoPagoState.isInitialized = true;
                                window.mercadoPagoState.instance = mp;
                                window.mercadoPagoState.publicKey = 'TEST-FALLBACK';

                                console.log('⚠️ MercadoPago inicializado com chave de fallback');
                                resolve(mp);
                            }, 100);
                        } catch (fallbackError) {
                            console.error('❌ Erro no fallback:', fallbackError);
                            reject(fallbackError);
                        }
                    } else {
                        console.error('❌ SDK não disponível para fallback');
                        reject(error);
                    }
                });
        } catch (error) {
            console.error('❌ Erro na inicialização do MercadoPago:', error);
            reject(error);
        }
    }

    // Flag para evitar múltiplas inicializações
    var autoInitAttempted = false;

    // Inicializar automaticamente quando o DOM estiver pronto
    function autoInitialize() {
        if (autoInitAttempted) {
            console.log('🔄 Auto-inicialização já tentada, pulando...');
            return;
        }
        
        autoInitAttempted = true;
        console.log('🎯 Auto-inicializando MercadoPago...');
        
        window.initializeMercadoPago()
            .then(function(mp) {
                console.log('🎉 MercadoPago auto-inicializado com sucesso');
                
                // Disparar evento personalizado
                var event = new CustomEvent('mercadoPagoReady', {
                    detail: { instance: mp }
                });
                window.dispatchEvent(event);
            })
            .catch(function(error) {
                console.error('❌ Erro na auto-inicialização:', error);
                autoInitAttempted = false; // Permitir nova tentativa em caso de erro
                
                // Disparar evento de erro
                var event = new CustomEvent('mercadoPagoError', {
                    detail: { error: error }
                });
                window.dispatchEvent(event);
            });
    }

    // Listener específico para quando o SDK do MercadoPago é carregado
    window.addEventListener('mercadoPagoSDKLoaded', function() {
        console.log('🎯 SDK do MercadoPago carregado - iniciando auto-inicialização...');
        if (!autoInitAttempted) {
            autoInitialize();
        }
    });

    // Event listeners para diferentes estados de carregamento
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Aguardar um pouco para garantir que o SDK foi carregado
            setTimeout(function() {
                if (typeof MercadoPago !== 'undefined' && !autoInitAttempted) {
                    autoInitialize();
                }
            }, 100);
        });
    } else if (document.readyState === 'interactive' || document.readyState === 'complete') {
        // DOM já carregado, verificar se SDK está disponível
        if (typeof MercadoPago !== 'undefined') {
            setTimeout(autoInitialize, 100);
        } else {
            // Aguardar SDK carregar
            setTimeout(function() {
                if (typeof MercadoPago !== 'undefined' && !autoInitAttempted) {
                    autoInitialize();
                }
            }, 1000);
        }
    }

    // Listener para quando a página é totalmente carregada (fallback)
    window.addEventListener('load', function() {
        if (!window.mercadoPagoState.isInitialized && !autoInitAttempted) {
            console.log('🔄 Página carregada, verificando MercadoPago...');
            if (typeof MercadoPago !== 'undefined') {
                autoInitialize();
            } else {
                console.error('❌ MercadoPago ainda não disponível após page load');
            }
        }
    });

    // Função de debugging
    window.debugMercadoPago = function() {
        console.log('🐛 Debug MercadoPago:');
        console.log('- SDK disponível:', typeof MercadoPago !== 'undefined');
        console.log('- Estado:', window.mercadoPagoState);
        console.log('- Função disponível:', typeof window.initializeMercadoPago === 'function');
        console.log('- Instância:', window.mercadoPagoState.instance);
    };

    console.log('✅ Módulo MercadoPago configurado');

})();
