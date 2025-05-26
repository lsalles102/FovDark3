
# 🚀 Guia de Deploy no Railway

## Passos para Deploy Completo

### 1. Configurar Variáveis de Ambiente no Railway

No painel do Railway, adicione estas variáveis:

```
JWT_SECRET_KEY=sua_chave_super_secreta_aqui_123456789
MERCADOPAGO_ACCESS_TOKEN=TEST-1234... (opcional)
EMAIL_HOST_USER=seu_email@gmail.com (opcional)
EMAIL_HOST_PASSWORD=sua_senha_app (opcional)
```

### 2. Banco de Dados PostgreSQL

- Railway criará automaticamente o PostgreSQL
- A variável `DATABASE_URL` será configurada automaticamente
- Não precisa configurar nada manualmente

### 3. Deploy Automático

- Railway detectará o `railway.json` e `nixpacks.toml`
- Build será feito automaticamente
- Aplicação ficará online em poucos minutos

## ✅ Funcionalidades Incluídas

- Sistema de autenticação completo
- Painel admin com gerenciamento de usuários
- Gerenciamento de produtos
- Editor de temas
- Sistema de pagamentos (quando configurado)
- Interface cyberpunk responsiva

## 🔧 Troubleshooting

Se houver erro no deploy:
1. Verifique se `JWT_SECRET_KEY` está configurada
2. Aguarde o PostgreSQL ser criado (1-2 minutos)
3. O sistema funcionará mesmo sem MercadoPago configurado

## 📧 Configuração de Email (Opcional)

Para ativar emails de recuperação de senha:
1. Configure `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD`
2. Use senha de aplicativo do Gmail, não a senha normal
