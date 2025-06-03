// Inicialização global do MercadoPago
(function() {
    'use strict';

    console.log('🔧 Iniciando configuração do MercadoPago...');

    // Verificar se já foi inicializado
    if (window.mercadoPagoInitialized) {
        console.log('✅ MercadoPago já inicializado');
        return;
    }

    let attempts = 0;
    const maxAttempts = 100; // 10 segundos máximo

    // Aguardar SDK estar carregado
    function initMercadoPago() {
        attempts++;

        // Verificar se MercadoPago está disponível globalmente
        if (typeof window.MercadoPago === 'undefined' && typeof MercadoPago === 'undefined') {
            if (attempts < maxAttempts) {
                console.log(`⏳ Aguardando SDK do MercadoPago... (tentativa ${attempts}/${maxAttempts})`);
                setTimeout(initMercadoPago, 100);
            } else {
                console.error('❌ Timeout: SDK do MercadoPago não carregou após', maxAttempts * 100, 'ms');
                // Tentar recarregar o SDK
                loadMercadoPagoSDK();
            }
            return;
        }

        try {
            // Usar MercadoPago global ou window.MercadoPago
            const MPClass = window.MercadoPago || MercadoPago;
            
            // Inicializar apenas uma vez
            if (!window.mercadoPagoInstance && MPClass) {
                // Usar chave pública padrão
                const publicKey = 'TEST-c8c68306-c9a2-4ec8-98db-0b00ad3c6dd9';

                window.mercadoPagoInstance = new MPClass(publicKey, {
                    locale: 'pt-BR'
                });

                console.log('✅ MercadoPago SDK inicializado globalmente');
                window.mercadoPagoInitialized = true;

                // Disparar evento customizado
                window.dispatchEvent(new CustomEvent('mercadopagoReady', {
                    detail: { instance: window.mercadoPagoInstance }
                }));
            }
        } catch (error) {
            console.error('❌ Erro ao inicializar MercadoPago:', error);

            // Tentar novamente após um delay
            setTimeout(() => {
                console.log('🔄 Tentando inicializar MercadoPago novamente...');
                window.mercadoPagoInitialized = false;
                window.mercadoPagoInstance = null;
                attempts = Math.max(0, attempts - 10); // Reduzir tentativas para não ficar infinito
                initMercadoPago();
            }, 2000);
        }
    }

    // Função para carregar o SDK manualmente se necessário
    function loadMercadoPagoSDK() {
        console.log('🔄 Tentando recarregar SDK do MercadoPago...');

        // Remover script existente se houver
        const existingScript = document.querySelector('script[src*="mercadopago.com"]');
        if (existingScript) {
            existingScript.remove();
        }

        // Adicionar novo script
        const script = document.createElement('script');
        script.src = 'https://sdk.mercadopago.com/js/v2';
        script.type = 'text/javascript';
        script.async = true;
        script.onload = () => {
            console.log('✅ SDK do MercadoPago recarregado');
            attempts = 0;
            setTimeout(initMercadoPago, 500);
        };
        script.onerror = () => {
            console.error('❌ Falha ao recarregar SDK do MercadoPago');
        };

        document.head.appendChild(script);
    }

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMercadoPago);
    } else {
        // Adicionar um pequeno delay para garantir que outros scripts carreguem
        setTimeout(initMercadoPago, 100);
    }

    // Expor função global para verificação
    window.isMercadoPagoReady = function() {
        return window.mercadoPagoInitialized && window.mercadoPagoInstance;
    };

    console.log('🎯 Configuração do MercadoPago preparada');
})();