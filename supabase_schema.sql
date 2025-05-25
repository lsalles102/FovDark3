-- FovDark - Schema completo para Supabase
-- Execute este arquivo no Supabase SQL Editor

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    data_expiracao TIMESTAMP NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de pagamentos
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    valor DECIMAL(10,2) NOT NULL,
    data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'completed',
    plano VARCHAR(50) NULL,
    gateway_id VARCHAR(255) NULL
);

-- Tabela de logs administrativos
CREATE TABLE IF NOT EXISTS admin_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    target_table VARCHAR(50) NOT NULL,
    target_id INTEGER NULL,
    details TEXT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_admin ON users(is_admin);
CREATE INDEX IF NOT EXISTS idx_users_expiration ON users(data_expiracao);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_timestamp ON admin_logs(timestamp);

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para atualizar updated_at na tabela users
CREATE OR REPLACE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Inserir usuário administrador padrão
INSERT INTO users (email, senha_hash, is_admin, data_expiracao) 
VALUES (
    'admin@darkfov.com', 
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 
    true, 
    '2025-12-31 23:59:59'
) ON CONFLICT (email) DO NOTHING;

-- RLS (Row Level Security) - Opcional para segurança extra
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_logs ENABLE ROW LEVEL SECURITY;

-- Políticas RLS básicas (podem ser ajustadas conforme necessário)
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid()::text = id::text OR is_admin = true);

CREATE POLICY "Admins can manage users" ON users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND is_admin = true
        )
    );

CREATE POLICY "Users can view own payments" ON payments
    FOR SELECT USING (
        user_id::text = auth.uid()::text OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND is_admin = true
        )
    );

CREATE POLICY "Only admins can view logs" ON admin_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND is_admin = true
        )
    );

-- Comentários nas tabelas
COMMENT ON TABLE users IS 'Tabela de usuários do sistema FovDark';
COMMENT ON TABLE payments IS 'Histórico de pagamentos e compras';
COMMENT ON TABLE admin_logs IS 'Logs de ações administrativas';

COMMENT ON COLUMN users.email IS 'Email único do usuário';
COMMENT ON COLUMN users.senha_hash IS 'Hash bcrypt da senha';
COMMENT ON COLUMN users.data_expiracao IS 'Data de expiração da licença';
COMMENT ON COLUMN users.is_admin IS 'Indica se o usuário é administrador';

COMMENT ON COLUMN payments.valor IS 'Valor do pagamento em reais';
COMMENT ON COLUMN payments.plano IS 'Tipo do plano: mensal, trimestral, anual';
COMMENT ON COLUMN payments.gateway_id IS 'ID do gateway de pagamento externo';

-- Verificar se tudo foi criado corretamente
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'payments', 'admin_logs');