
# 🏭 Configuração MercadoPago para Produção

## 📋 Passos para Ativar Pagamentos Reais

### 1. Criar Conta no MercadoPago
- Acesse [mercadopago.com.br](https://mercadopago.com.br)
- Crie sua conta empresarial
- Complete a verificação de identidade

### 2. Obter Credenciais de Produção
- Acesse [developers.mercadopago.com](https://developers.mercadopago.com)
- Faça login com sua conta
- Vá em **"Suas integrações"**
- Clique em **"Credenciais"**
- Copie o **Access Token de Produção** (começa com `APP_USR_`)

### 3. Configurar no Replit
- No seu Repl, clique no ícone **🔒 Secrets** na barra lateral
- Adicione uma nova variável:
  - **Chave:** `MERCADOPAGO_ACCESS_TOKEN`
  - **Valor:** Seu Access Token de produção

### 4. Configurar Webhook no MercadoPago
- No painel do MercadoPago, vá em **"Webhooks"**
- Adicione a URL: `https://SEU-REPL.replit.dev/api/webhook/mercadopago`
- Selecione os eventos: **payment**

### 5. Verificar Configuração
- Acesse `/api/mercadopago/status` no seu site
- Deve mostrar: **"MercadoPago configurado em modo PRODUÇÃO"**

## ⚠️ Diferenças entre Teste e Produção

### Modo Teste (Token com "TEST")
- ✅ Pagamentos simulados
- ✅ Cartões de teste
- ❌ Dinheiro não é transferido

### Modo Produção (Token "APP_USR_")
- ✅ Pagamentos reais
- ✅ Dinheiro transferido para sua conta
- ⚠️ Taxas do MercadoPago aplicadas

## 💳 Métodos de Pagamento Disponíveis
- PIX (instantâneo)
- Cartão de crédito (até 12x)
- Cartão de débito
- Boleto bancário

## 🔒 Segurança
- Todos os pagamentos são processados pelo MercadoPago
- Dados do cartão nunca passam pelo seu servidor
- Certificação PCI-DSS

## 📊 Acompanhamento
- Dashboard do MercadoPago para vendas
- Relatórios financeiros
- Conciliação automática
