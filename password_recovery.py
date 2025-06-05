import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from models import User, PasswordResetToken
from email_utils import send_email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def generate_recovery_token() -> str:
    """Gerar token seguro para recuperação de senha"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


def create_password_reset_token(db: Session, user_id: int) -> str:
    """Criar token de recuperação de senha"""
    # Invalidar tokens anteriores do usuário
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used == False
    ).update({"used": True})
    
    # Criar novo token
    token = generate_recovery_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)  # Token válido por 1 hora
    
    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(reset_token)
    db.commit()
    
    return token


def verify_reset_token(db: Session, token: str) -> Optional[User]:
    """Verificar se o token de recuperação é válido"""
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if reset_token:
        return reset_token.user
    return None


def use_reset_token(db: Session, token: str) -> bool:
    """Marcar token como usado"""
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False
    ).first()
    
    if reset_token:
        reset_token.used = True
        db.commit()
        return True
    return False


def send_recovery_email_sendgrid(email: str, recovery_token: str) -> bool:
    """Enviar email de recuperação usando SendGrid"""
    try:
        # Obter configurações do domínio
        from domain_config import get_production_domain
        base_url = get_production_domain()
        recovery_link = f"{base_url}/recover?token={recovery_token}"
        
        # Template HTML para recuperação de senha
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recuperação de Senha - FovDark</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: #0a0a0a; 
                    color: #ffffff; 
                    margin: 0; 
                    padding: 20px;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #1a1a1a;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(255, 107, 107, 0.3);
                }}
                .header {{
                    background: linear-gradient(135deg, #ff6b6b, #ffd93d, #ff6b6b);
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                }}
                .header::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
                    animation: shine 3s infinite;
                }}
                @keyframes shine {{
                    0% {{ transform: translateX(-100%); }}
                    100% {{ transform: translateX(100%); }}
                }}
                .logo {{
                    font-size: 2.5em;
                    font-weight: bold;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }}
                .header h2 {{
                    margin: 0;
                    font-size: 1.5em;
                    font-weight: 300;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .content h3 {{
                    color: #ff6b6b;
                    margin-top: 0;
                    font-size: 1.3em;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #ff6b6b, #ff5252);
                    color: #ffffff !important;
                    padding: 15px 40px;
                    text-decoration: none;
                    border-radius: 50px;
                    font-weight: bold;
                    margin: 25px 0;
                    font-size: 16px;
                    transition: all 0.3s ease;
                    box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
                }}
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(255, 107, 107, 0.6);
                }}
                .warning {{
                    background: rgba(255, 107, 107, 0.1);
                    border-left: 4px solid #ff6b6b;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 0 8px 8px 0;
                }}
                .footer {{
                    background: #0a0a0a;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #333;
                }}
                .footer p {{
                    margin: 5px 0;
                    font-size: 14px;
                    color: #888;
                }}
                .link-backup {{
                    background: #2a2a2a;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    word-break: break-all;
                    font-family: monospace;
                    font-size: 12px;
                    color: #ccc;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔐 FovDark</div>
                    <h2>Recuperação de Senha</h2>
                </div>
                <div class="content">
                    <h3>Olá!</h3>
                    <p>Você solicitou a recuperação de senha para sua conta no <strong>FovDark</strong>.</p>
                    <p>Para redefinir sua senha de forma segura, clique no botão abaixo:</p>
                    
                    <center>
                        <a href="{recovery_link}" class="button">🔑 Redefinir Minha Senha</a>
                    </center>
                    
                    <div class="warning">
                        <p><strong>⚠️ Importante:</strong></p>
                        <ul>
                            <li>Este link é válido por apenas <strong>1 hora</strong></li>
                            <li>Só pode ser usado uma única vez</li>
                            <li>Se você não solicitou esta recuperação, ignore este email</li>
                        </ul>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #333; margin: 30px 0;">
                    
                    <p><strong>Link não está funcionando?</strong></p>
                    <p>Copie e cole este endereço no seu navegador:</p>
                    <div class="link-backup">{recovery_link}</div>
                </div>
                <div class="footer">
                    <p><strong>FovDark Security Team</strong></p>
                    <p>© 2025 FovDark. Todos os direitos reservados.</p>
                    <p>Este é um email automático, não responda a esta mensagem.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Usar a função send_email do email_utils.py
        success = send_email(
            to_email=email,
            subject="🔐 Recuperação de Senha - FovDark",
            html_content=html_content
        )
        
        if success:
            print(f"Email de recuperação enviado para {email} via SendGrid")
            return True
        else:
            print(f"Falha ao enviar email de recuperação para {email}")
            return False
            
    except Exception as e:
        print(f"Erro ao enviar email de recuperação via SendGrid: {e}")
        return False


def send_recovery_email_simple(email: str, recovery_token: str) -> bool:
    """Versão simplificada que sempre retorna True para desenvolvimento"""
    print(f"EMAIL DE RECUPERAÇÃO SIMULADO")
    print(f"Para: {email}")
    print(f"Token: {recovery_token}")
    print(f"Link: http://localhost:5000/recover?token={recovery_token}")
    print("-" * 50)
    return True