
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_recovery_email(email: str, token: str):
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Recuperação de Senha - DarkFov"
    message["From"] = sender_email
    message["To"] = email
    
    recovery_link = f"https://darkfov.repl.co/reset-password/{token}"
    
    html = f"""
    <html>
        <body>
            <h2>Recuperação de Senha - DarkFov</h2>
            <p>Você solicitou a recuperação de senha. Clique no link abaixo:</p>
            <p><a href="{recovery_link}">Resetar Senha</a></p>
            <p>Se você não solicitou esta recuperação, ignore este email.</p>
        </body>
    </html>
    """
    
    message.attach(MIMEText(html, "html"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
