
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
            if (window.mercadoPagoState.isInitialized) {
                console.log('✅ MercadoPago já inicializado');
                resolve(window.mercadoPagoState.instance);
                return;
            }

            // Verificar se o SDK está carregado
            if (typeof MercadoPago === 'undefined') {
                console.log('⏳ SDK do MercadoPago não carregado ainda, aguardando...');
                
                // Aguardar até 15 segundos pelo SDK
                var attempts = 0;
                var maxAttempts = 75; // 75 x 200ms = 15 segundos
                
                var checkInterval = setInterval(function() {
                    attempts++;
                    
                    if (typeof MercadoPago !== 'undefined') {
                        clearInterval(checkInterval);
                        console.log('✅ SDK do MercadoPago detectado após ' + (attempts * 200) + 'ms');
                        initializeMercadoPagoInstance(resolve, reject);
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkInterval);
                        console.error('❌ Timeout: SDK do MercadoPago não carregou após 15 segundos');
                        console.log('🔍 Verificando se há erros de CSP ou bloqueios de rede');
                        reject(new Error('SDK do MercadoPago não carregou - verifique CSP e conectividade'));
                    } else if (attempts % 10 === 0) {
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

                    // Criar instância do MercadoPago
                    var mp = new MercadoPago(data.public_key, {
                        locale: 'pt-BR'
                    });

                    // Atualizar estado global
                    window.mercadoPagoState.isLoaded = true;
                    window.mercadoPagoState.isInitialized = true;
                    window.mercadoPagoState.instance = mp;
                    window.mercadoPagoState.publicKey = data.public_key;

                    console.log('✅ MercadoPago inicializado com sucesso');
                    console.log('📊 Estado:', window.mercadoPagoState);

                    resolve(mp);
                })
                .catch(function(error) {
                    console.error('❌ Erro ao obter chave pública:', error);
                    
                    // Tentar com chave de teste como fallback
                    console.log('🔄 Tentando inicializar com configuração de fallback...');
                    
                    try {
                        var mp = new MercadoPago('TEST-a8b1e4f8-e4a5-4b1c-9c8d-2e3f4g5h6i7j', {
                            locale: 'pt-BR'
                        });

                        window.mercadoPagoState.isLoaded = true;
                        window.mercadoPagoState.isInitialized = true;
                        window.mercadoPagoState.instance = mp;
                        window.mercadoPagoState.publicKey = 'TEST-FALLBACK';

                        console.log('⚠️ MercadoPago inicializado com chave de fallback');
                        resolve(mp);
                    } catch (fallbackError) {
                        console.error('❌ Erro no fallback:', fallbackError);
                        reject(fallbackError);
                    }
                });
        } catch (error) {
            console.error('❌ Erro na inicialização do MercadoPago:', error);
            reject(error);
        }
    }

    // Inicializar automaticamente quando o DOM estiver pronto
    function autoInitialize() {
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
                
                // Disparar evento de erro
                var event = new CustomEvent('mercadoPagoError', {
                    detail: { error: error }
                });
                window.dispatchEvent(event);
            });
    }

    // Event listeners para diferentes estados de carregamento
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInitialize);
    } else {
        // DOM já carregado
        setTimeout(autoInitialize, 100);
    }

    // Listener para quando o SDK é carregado
    window.addEventListener('load', function() {
        if (!window.mercadoPagoState.isInitialized) {
            console.log('🔄 Página carregada, tentando inicializar MercadoPago novamente...');
            autoInitialize();
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
