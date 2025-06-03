
// Inicialização global do MercadoPago
(function() {
    'use strict';
    
    // Verificar se já foi inicializado
    if (window.mercadoPagoInitialized) {
        return;
    }
    
    // Aguardar SDK estar carregado
    function initMercadoPago() {
        if (typeof MercadoPago === 'undefined') {
            console.log('⏳ Aguardando SDK do MercadoPago...');
            setTimeout(initMercadoPago, 100);
            return;
        }
        
        try {
            // Inicializar apenas uma vez
            if (!window.mercadoPagoInstance) {
                window.mercadoPagoInstance = new MercadoPago('TEST-c8c68306-c9a2-4ec8-98db-0b00ad3c6dd9', {
                    locale: 'pt-BR'
                });
                
                console.log('✅ MercadoPago SDK inicializado globalmente');
                window.mercadoPagoInitialized = true;
                
                // Disparar evento customizado
                window.dispatchEvent(new CustomEvent('mercadopagoReady'));
            }
        } catch (error) {
            console.error('❌ Erro ao inicializar MercadoPago:', error);
        }
    }
    
    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMercadoPago);
    } else {
        initMercadoPago();
    }
})();
