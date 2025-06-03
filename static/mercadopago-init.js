
// Inicialização segura do MercadoPago SDK
(function() {
    let mercadoPagoInstance = null;
    let isLoading = false;
    let isLoaded = false;

    // Função para verificar se MercadoPago está disponível
    function checkMercadoPagoAvailability() {
        return typeof window.MercadoPago !== 'undefined';
    }

    // Função para aguardar o carregamento do SDK
    function waitForMercadoPago() {
        return new Promise((resolve, reject) => {
            if (checkMercadoPagoAvailability()) {
                resolve(window.MercadoPago);
                return;
            }

            let attempts = 0;
            const maxAttempts = 50; // 5 segundos máximo
            
            const checkInterval = setInterval(() => {
                attempts++;
                
                if (checkMercadoPagoAvailability()) {
                    clearInterval(checkInterval);
                    resolve(window.MercadoPago);
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    reject(new Error('MercadoPago SDK não carregou no tempo esperado'));
                }
            }, 100);
        });
    }

    // Função principal de inicialização
    async function initializeMercadoPago() {
        if (isLoading) {
            console.log('⏳ MercadoPago já está carregando...');
            return;
        }

        if (isLoaded && mercadoPagoInstance) {
            console.log('✅ MercadoPago já está carregado');
            return mercadoPagoInstance;
        }

        try {
            isLoading = true;
            console.log('🔄 Aguardando carregamento do MercadoPago SDK...');
            
            const MercadoPago = await waitForMercadoPago();
            
            // Buscar chave pública
            const response = await fetch('/api/mercadopago/public-key');
            const data = await response.json();
            const publicKey = data.public_key;

            if (!publicKey) {
                throw new Error('Chave pública do MercadoPago não encontrada');
            }

            console.log('🔑 Chave pública obtida:', publicKey.substring(0, 20) + '...');

            // Inicializar MercadoPago
            mercadoPagoInstance = new MercadoPago(publicKey);
            
            console.log('✅ MercadoPago SDK inicializado com sucesso');
            
            // Disponibilizar globalmente
            window.mercadoPagoInstance = mercadoPagoInstance;
            window.MercadoPagoSDK = MercadoPago;
            
            isLoaded = true;
            isLoading = false;

            // Disparar evento personalizado
            window.dispatchEvent(new CustomEvent('mercadoPagoReady', { 
                detail: { instance: mercadoPagoInstance } 
            }));

            return mercadoPagoInstance;

        } catch (error) {
            console.error('❌ Erro ao inicializar MercadoPago:', error);
            isLoading = false;
            throw error;
        }
    }

    // Função para verificar se está disponível
    function isMercadoPagoAvailable() {
        return isLoaded && mercadoPagoInstance !== null;
    }

    // Expor funções globalmente
    window.initializeMercadoPago = initializeMercadoPago;
    window.isMercadoPagoAvailable = isMercadoPagoAvailable;
    window.getMercadoPagoInstance = function() {
        return mercadoPagoInstance;
    };

    // Auto-inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initializeMercadoPago, 500); // Aguardar um pouco para o SDK carregar
        });
    } else {
        setTimeout(initializeMercadoPago, 500);
    }

    console.log('✅ MercadoPago initialization script loaded');
})();
