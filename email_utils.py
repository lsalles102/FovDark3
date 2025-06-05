import os
import requests
import json
from sqlalchemy.orm import Session
from database import get_db
from models import SiteSettings

def get_sendgrid_settings():
    """Obter configurações do SendGrid"""
    return {
        "api_key": os.environ.get('SENDGRID_API_KEY'),
        "from_email": "noreply@fovdark.com",
        "from_name": "FovDark"
    }

def send_email(to_email, subject, html_content):
    """Enviar email usando SendGrid API REST"""
    try:
        # Obter chave API do SendGrid
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_key:
            print("SENDGRID_API_KEY não configurada")
            return False

        # URL da API SendGrid
        url = "https://api.sendgrid.com/v3/mail/send"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {sendgrid_key}",
            "Content-Type": "application/json"
        }
        
        # Dados do email
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": "noreply@fovdark.com",
                "name": "FovDark"
            },
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
        
        # Enviar request
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 202:
            print(f"✅ Email enviado para {to_email}")
            return True
        else:
            print(f"❌ Erro SendGrid - Status: {response.status_code}, Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Erro ao enviar email via SendGrid: {e}")
        return False

def send_confirmation_email(email):
    """Enviar email de confirmação de registro"""
    subject = "Bem-vindo ao FovDark!"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                font-family: Arial, sans-serif;
                background: #0a0a0a;
                color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #00ff88, #00ccff);
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .footer {{
                background: #1a1a1a;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #888;
            }}
            .button {{
                display: inline-block;
                background: #00ff88;
                color: #000;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🎯 FovDark</h1>
                <p>Bem-vindo ao futuro do gaming!</p>
            </div>
            <div class="content">
                <h2>Conta criada com sucesso!</h2>
                <p>Olá, <strong>{email}</strong>!</p>
                <p>Sua conta no FovDark foi criada com sucesso. Agora você pode:</p>
                <ul>
                    <li>Acessar seu painel de controle</li>
                    <li>Escolher um plano que se adeque às suas necessidades</li>
                    <li>Baixar nosso software após a compra</li>
                    <li>Receber suporte técnico especializado</li>
                </ul>
                <p>Pronto para dominar o campo de batalha?</p>
                <a href="https://fovdark.repl.co/comprar" class="button">ESCOLHER PLANO</a>
            </div>
            <div class="footer">
                <p>&copy; 2024 FovDark. Todos os direitos reservados.</p>
                <p>Este é um email automático, não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(email, subject, html_content)

def send_recovery_email(email, recovery_token):
    """Enviar email de recuperação de senha"""
    subject = "Recuperação de Senha - FovDark"
    recovery_link = f"https://fovdark.repl.co/reset-password/{recovery_token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                font-family: Arial, sans-serif;
                background: #0a0a0a;
                color: #ffffff;
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
            .footer {{
                background: #1a1a1a;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #888;
            }}
            .button {{
                display: inline-block;
                background: #ff6b6b;
                color: #fff;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .warning {{
                background: #2a1810;
                border-left: 4px solid #ff6b6b;
                padding: 15px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🔐 FovDark</h1>
                <p>Recuperação de Senha</p>
            </div>
            <div class="content">
                <h2>Solicitação de Nova Senha</h2>
                <p>Olá, <strong>{email}</strong>!</p>
                <p>Recebemos uma solicitação para redefinir a senha da sua conta FovDark.</p>

                <div class="warning">
                    <strong>⚠️ Importante:</strong> Se você não solicitou esta recuperação, ignore este email. Sua conta permanecerá segura.
                </div>

                <p>Para criar uma nova senha, clique no botão abaixo:</p>
                <a href="{recovery_link}" class="button">REDEFINIR SENHA</a>

                <p><strong>Este link expira em 1 hora por segurança.</strong></p>

                <p>Ou copie e cole este link no seu navegador:</p>
                <p style="word-break: break-all; background: #1a1a1a; padding: 10px; border-radius: 5px; font-family: monospace;">
                    {recovery_link}
                </p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FovDark. Todos os direitos reservados.</p>
                <p>Este é um email automático, não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(email, subject, html_content)

def send_purchase_confirmation(email, plan_name, expiration_date):
    """Enviar confirmação de compra"""
    subject = "Compra Confirmada - FovDark"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                font-family: Arial, sans-serif;
                background: #0a0a0a;
                color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #00ff88, #00ccff);
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .footer {{
                background: #1a1a1a;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #888;
            }}
            .button {{
                display: inline-block;
                background: #00ff88;
                color: #000;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .success-box {{
                background: #0f2419;
                border: 2px solid #00ff88;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>✅ Compra Confirmada!</h1>
                <p>Seu acesso está ativo!</p>
            </div>
            <div class="content">
                <h2>Parabéns, <strong>{email}</strong>!</h2>

                <div class="success-box">
                    <h3>🎯 Plano: {plan_name}</h3>
                    <p>Válido até: <strong>{expiration_date}</strong></p>
                </div>

                <p>Sua compra foi processada com sucesso! Agora você pode:</p>
                <ul>
                    <li>✅ Baixar o software FovDark</li>
                    <li>✅ Acessar todas as funcionalidades premium</li>
                    <li>✅ Receber suporte prioritário</li>
                    <li>✅ Participar da comunidade Discord exclusiva</li>
                </ul>

                <p>Acesse seu painel para baixar o software:</p>
                <a href="https://fovdark.repl.co/painel" class="button">ACESSAR PAINEL</a>

                <p><strong>🔒 Lembre-se:</strong> Mantenha suas credenciais seguras e não compartilhe seu acesso.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FovDark. Todos os direitos reservados.</p>
                <p>Precisa de ajuda? Entre em contato conosco.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(email, subject, html_content)