# 🚀 Guia de Migração para Supabase

## Passo a Passo Completo

### 1. **Configurar Projeto no Supabase**
- Acesse https://supabase.com
- Crie um novo projeto
- Anote o nome do projeto e senha do banco

### 2. **Executar Schema no Supabase**
- Vá em "SQL Editor" no painel do Supabase
- Cole todo o conteúdo do arquivo `supabase_schema.sql`
- Execute o script (vai criar todas as tabelas e usuário admin)

### 3. **Obter URL de Conexão**
- Em "Settings" > "Database"
- Copie a "Connection string"
- Formato: `postgresql://postgres:[SUA_SENHA]@db.[PROJETO].supabase.co:5432/postgres`

### 4. **Configurar Variáveis de Ambiente**
```env
DATABASE_URL=postgresql://postgres:[SUA_SENHA]@db.[PROJETO].supabase.co:5432/postgres
SECRET_KEY=darkfov-super-secret-key-2024
```

### 5. **Deploy no Railway/Vercel**
- Supabase funciona perfeitamente com qualquer plataforma
- Configure apenas a variável `DATABASE_URL` com a string do Supabase
- O resto permanece igual

## ✅ **Vantagens do Supabase:**
- **Gratuito** até 500MB
- **Backup automático**
- **Interface administrativa** 
- **APIs REST automáticas**
- **Real-time** (se precisar no futuro)
- **Logs detalhados**

## 🎯 **Arquivos Criados:**
- `supabase_schema.sql` - Schema completo para executar
- `supabase_config.py` - Configuração alternativa (opcional)
- Este guia com instruções

## 👤 **Credenciais Admin Já Criadas:**
- Email: `admin@darkfov.com`
- Senha: `secret`

Tudo pronto para usar! O Supabase é muito mais estável que bancos locais e vai dar zero problemas no deploy.