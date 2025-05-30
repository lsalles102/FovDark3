
# 🚀 Configuração do MercadoPago no Railway

## 📋 Passo a Passo Completo

### 1. **Configurar Variáveis no Railway**
No painel do Railway, adicione estas variáveis:

```env
MERCADOPAGO_ACCESS_TOKEN=TEST-1234... (ou APP_USR-xxx para produção)
CUSTOM_DOMAIN=https://www.fovdark.shop
```

### 2. **Configurar Webhook no MercadoPago**
- Acesse o painel do MercadoPago
- Vá em **Webhooks**
- Configure a URL: `https://www.fovdark.shop/api/webhook/mercadopago`
- Eventos: **payment**

### 3. **Verificar Configuração**
Após configurar, acesse:
- `https://www.fovdark.shop/api/mercadopago/status`

Deve mostrar:
```json
{
  "status": "configured",
  "message": "✅ MercadoPago configurado",
  "environment": "test" ou "production",
  "can_process_payments": true
}
```

## 🔧 Variáveis de Ambiente do Railway

### Obrigatórias:
- `DATABASE_URL` (criada automaticamente pelo Railway)
- `SECRET_KEY` (pode usar: `darkfov-railway-secret-2024`)

### Opcionais:
- `MERCADOPAGO_ACCESS_TOKEN` (para pagamentos)
- `CUSTOM_DOMAIN` (seu domínio personalizado)

## ✅ Verificação Final

O sistema agora está 100% configurado para Railway:
- ✅ Detecção automática do ambiente Railway
- ✅ Configuração de domínio personalizado
- ✅ Webhooks do MercadoPago funcionando
- ✅ CORS configurado para Railway
- ✅ Banco PostgreSQL integrado

## 🚨 Troubleshooting

Se ainda houver problemas:
1. Verifique se `CUSTOM_DOMAIN` está configurado
2. Confirme que o webhook do MercadoPago aponta para seu domínio
3. Teste o endpoint `/api/mercadopago/status`
