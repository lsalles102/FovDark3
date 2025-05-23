# DarkFov - Sistema de Vendas

Sistema completo de vendas e autenticação para produto digital (aimbot para BloodStrike) com tema cyberpunk.

## 🚀 Deploy no Railway

### Pré-requisitos
1. Conta no Railway (https://railway.app)
2. Repositório GitHub com o código

### Passos para Deploy

1. **Conectar com GitHub**
   - Faça login no Railway
   - Conecte sua conta GitHub
   - Importe este repositório

2. **Configurar Banco PostgreSQL**
   - No Railway, adicione um serviço PostgreSQL
   - O Railway criará automaticamente a variável `DATABASE_URL`

3. **Configurar Variáveis de Ambiente**
   ```
   DATABASE_URL=postgresql://... (automático do Railway)
   SECRET_KEY=sua-chave-secreta-jwt-aqui
   ```

4. **Deploy Automático**
   - O Railway detectará automaticamente os arquivos de configuração
   - O deploy será feito usando o `nixpacks.toml`

### Funcionalidades

- ✅ Sistema de autenticação JWT
- ✅ Registro e login de usuários
- ✅ Painel administrativo completo
- ✅ Processamento de pagamentos
- ✅ Controle de licenças
- ✅ Download protegido de arquivos
- ✅ Tema cyberpunk responsivo

### Credenciais de Admin
- Email: `admin@darkfov.com`
- Senha: `secret`

### Tecnologias
- FastAPI (Python)
- PostgreSQL
- JWT Authentication
- Jinja2 Templates
- CSS3 + JavaScript vanilla

## 🎮 Uso

1. Acesse a aplicação
2. Registre uma conta ou use as credenciais admin
3. Navegue pelos planos de pagamento
4. Gerencie usuários no painel admin
5. Faça download do script (apenas com licença ativa)