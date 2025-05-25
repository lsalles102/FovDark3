
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_confirmation_email(email: str):
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Bem-vindo ao DarkFov"
    message["From"] = sender_email
    message["To"] = email
    
    html = f"""
    <html>
        <body>
            <h2>Bem-vindo ao DarkFov</h2>
            <p>Sua conta foi criada com sucesso!</p>
            <p>Acesse nosso site para fazer login e começar a usar:</p>
            <p><a href="https://darkfov.repl.co/login">Fazer Login</a></p>
        </body>
    </html>
    """
    
    message.attach(MIMEText(html, "html"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())

def send_recovery_email(email: str, token: str):
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    
    if not sender_email or not sender_password:
        raise Exception("Configurações de email não encontradas. Configure SMTP_EMAIL e SMTP_PASSWORD no Secrets.")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Recuperação de Senha - FovDark"
    message["From"] = sender_email
    message["To"] = email
    
    # Obter a URL base do projeto
    base_url = os.getenv("REPL_URL", "https://fovdark-system.replit.app")
    recovery_link = f"{base_url}/reset-password/{token}"
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #0a0a0f; color: #e0e0e0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1a1a2e; border-radius: 10px; padding: 30px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #00fff7; font-size: 32px; margin: 0;">FovDark</h1>
                    <p style="color: #ff00c8; font-size: 14px; margin: 0;">SISTEMA DE RECUPERAÇÃO</p>
                </div>
                
                <h2 style="color: #00fff7; border-bottom: 2px solid #ff00c8; padding-bottom: 10px;">
                    Recuperação de Senha
                </h2>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    Olá! Você solicitou a recuperação de senha para sua conta FovDark.
                </p>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    Clique no botão abaixo para definir uma nova senha:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{recovery_link}" 
                       style="display: inline-block; background: linear-gradient(45deg, #00fff7, #ff00c8); 
                              color: #000; text-decoration: none; padding: 15px 30px; 
                              border-radius: 25px; font-weight: bold; font-size: 16px;">
                        REDEFINIR SENHA
                    </a>
                </div>
                
                <p style="font-size: 14px; line-height: 1.6; color: #b0b0b0;">
                    Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
                </p>
                
                <p style="word-break: break-all; background-color: #0a0a0f; padding: 10px; 
                          border-radius: 5px; font-family: monospace; font-size: 12px;">
                    {recovery_link}
                </p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #333;">
                    <p style="font-size: 14px; color: #888;">
                        <strong>Importante:</strong><br>
                        • Este link expira em 1 hora<br>
                        • Se você não solicitou esta recuperação, ignore este email<br>
                        • Nunca compartilhe este link com terceiros
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p style="font-size: 12px; color: #666;">
                        © 2024 FovDark - Sistema de Controle Absoluto
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    text = f"""
    FovDark - Recuperação de Senha
    
    Você solicitou a recuperação de senha para sua conta.
    
    Acesse o link abaixo para redefinir sua senha:
    {recovery_link}
    
    Este link expira em 1 hora.
    
    Se você não solicitou esta recuperação, ignore este email.
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    
    message.attach(part1)
    message.attach(part2)
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
    except Exception as e:
        raise Exception(f"Erro ao enviar email: {str(e)}")
