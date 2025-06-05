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


def send_recovery_email_smtp(email: str, recovery_token: str) -> bool:
    """Enviar email de recuperação usando SMTP"""
    try:
        # Configurações SMTP (usar Gmail como exemplo)
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        if not smtp_user or not smtp_password:
            print("Configurações SMTP não encontradas")
            return False
        
        # Criar link de recuperação
        base_url = os.getenv("BASE_URL", "http://localhost:5000")
        recovery_link = f"{base_url}/recover?token={recovery_token}"
        
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Recuperação de Senha - FovDark"
        msg['From'] = smtp_user
        msg['To'] = email
        
        # Template HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    background: #0a0a0a; 
                    color: #ffffff; 
                    margin: 0; 
                    padding: 20px; 
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #1a1a1a;
                    border-radius: 10px;
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #ff6b6b, #ffd93d);
                    padding: 30px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                }}
                .button {{
                    display: inline-block;
                    background: #ff6b6b;
                    color: #ffffff !important;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #0a0a0a;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #888;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 FovDark</h1>
                    <h2>Recuperação de Senha</h2>
                </div>
                <div class="content">
                    <p>Olá,</p>
                    <p>Você solicitou a recuperação de senha para sua conta no FovDark.</p>
                    <p>Clique no botão abaixo para redefinir sua senha:</p>
                    <center>
                        <a href="{recovery_link}" class="button">Redefinir Senha</a>
                    </center>
                    <p><strong>Este link é válido por apenas 1 hora.</strong></p>
                    <p>Se você não solicitou esta recuperação, ignore este email.</p>
                    <hr>
                    <p><small>Se o botão não funcionar, copie e cole este link no seu navegador:</small></p>
                    <p><small>{recovery_link}</small></p>
                </div>
                <div class="footer">
                    <p>© 2025 FovDark. Todos os direitos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Enviar email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, email, msg.as_string())
        
        print(f"Email de recuperação enviado para {email}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email de recuperação: {e}")
        return False


def send_recovery_email_simple(email: str, recovery_token: str) -> bool:
    """Versão simplificada que sempre retorna True para desenvolvimento"""
    print(f"EMAIL DE RECUPERAÇÃO SIMULADO")
    print(f"Para: {email}")
    print(f"Token: {recovery_token}")
    print(f"Link: http://localhost:5000/recover?token={recovery_token}")
    print("-" * 50)
    return True