
# Configuração de Email para Recuperação de Senha

## Variáveis de Ambiente Necessárias

Para que o sistema de recuperação de senha funcione, você precisa configurar as seguintes variáveis no **Secrets** do Replit:

### 1. SMTP_EMAIL
- **Descrição**: Email que será usado para enviar os emails de recuperação
- **Exemplo**: `seuemail@gmail.com`
- **Tipo**: Gmail recomendado

### 2. SMTP_PASSWORD
- **Descrição**: Senha de aplicativo do Gmail (não a senha normal)
- **Como obter**:
  1. Acesse sua conta Google
  2. Vá em "Gerenciar sua conta Google"
  3. Na aba "Segurança", ative a "Verificação em duas etapas"
  4. Depois vá em "Senhas de app"
  5. Gere uma senha para "Email"
  6. Use essa senha gerada

### 3. REPL_URL (Opcional)
- **Descrição**: URL do seu projeto Replit
- **Exemplo**: `https://fovdark-system.replit.app`
- **Padrão**: Se não configurado, usa o valor padrão

## Como Configurar no Replit

1. No seu Repl, clique na aba "Secrets" (ícone de cadeado)
2. Adicione cada variável:
   - Key: `SMTP_EMAIL`
   - Value: `seuemail@gmail.com`
   
   - Key: `SMTP_PASSWORD`
   - Value: `sua_senha_de_aplicativo`

3. Reinicie o servidor

## Teste o Sistema

1. Acesse `/recover-password`
2. Digite um email válido cadastrado
3. Verifique se o email foi recebido
4. Clique no link e redefina a senha

## Troubleshooting

### Email não chegou?
- Verifique spam/lixo eletrônico
- Confirme se as credenciais SMTP estão corretas
- Verifique se a verificação em duas etapas está ativa no Gmail

### Erro de autenticação?
- Use senha de aplicativo, não a senha normal
- Confirme se o email está correto

### Link não funciona?
- Verifique se REPL_URL está configurado corretamente
- O link expira em 1 hora
