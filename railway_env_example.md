
# 🚀 Configuração de Variáveis de Ambiente - Railway

## Variáveis Obrigatórias

### 1. **DATABASE_URL**
```
postgresql://username:password@host:port/database
```
*Esta será gerada automaticamente quando você adicionar PostgreSQL no Railway*

### 2. **SECRET_KEY**
```
darkfov-super-secret-key-2024-railway
```
*Chave secreta para JWT - você pode gerar uma nova*

## Variáveis Opcionais

### 3. **MERCADOPAGO_ACCESS_TOKEN** (Opcional)
```
APP_USR-1234567890123456-123456-abcdef1234567890abcdef1234567890-123456789
```
*Token do MercadoPago - deixe vazio se não for usar pagamentos ainda*

### 4. **EMAIL_PASSWORD** (Opcional) 
```
sua_senha_do_email_aqui
```
*Senha do email para recuperação de senha - opcional*

## 🔧 Como Configurar no Railway

1. **Acesse seu projeto no Railway**
2. **Vá em "Variables"**
3. **Adicione cada variável:**
   - Nome: `SECRET_KEY`
   - Valor: `darkfov-super-secret-key-2024-railway`
4. **Para PostgreSQL:**
   - Clique em "+ New"
   - Selecione "Database" → "PostgreSQL"
   - A `DATABASE_URL` será criada automaticamente

## ✅ Deploy Funcionando

Com essas configurações, seu FovDark vai funcionar perfeitamente:
- ✅ Sistema funcionando sem MercadoPago (opcional)
- ✅ Banco PostgreSQL configurado
- ✅ Autenticação JWT funcionando
- ✅ Painel admin acessível

**Credenciais Admin:**
- Email: `admin@fovdark.com`
- Senha: `secret`
