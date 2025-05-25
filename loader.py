
import tkinter as tk
from tkinter import messagebox
import requests
import subprocess
import os

# URL do seu projeto no Replit
API_URL = "https://darkfov.repl.co"
LOGIN_URL = f"{API_URL}/api/login"
LICENSE_URL = f"{API_URL}/api/license/check"
DOWNLOAD_URL = f"{API_URL}/api/download/executable"
EXECUTAVEL = "Script_Dark.exe"

def login():
    email = entry_email.get()
    senha = entry_senha.get()
    
    if not email or not senha:
        messagebox.showwarning("Campos obrigatórios", "Preencha email e senha.")
        return

    try:
        # Login usando Form data conforme o sistema atual
        data = {"email": email, "password": senha}
        res = requests.post(LOGIN_URL, data=data)
        
        if res.status_code != 200:
            messagebox.showerror("Erro", "Login inválido.")
            return
            
        token = res.json()["access_token"]
    except Exception as e:
        messagebox.showerror("Erro", f"Falha na conexão com o servidor: {str(e)}")
        return

    # Verifica licença
    headers = {"Authorization": f"Bearer {token}"}
    try:
        lic = requests.get(LICENSE_URL, headers=headers)
        if lic.status_code != 200:
            messagebox.showwarning("Licença inválida", "Sua licença está expirada ou inválida.")
            return
            
        license_data = lic.json()
        if not license_data.get("valid", False):
            messagebox.showwarning("Licença inválida", "Sua licença está expirada ou inválida.")
            return
            
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar licença: {str(e)}")
        return

    # Baixa o executável
    try:
        res = requests.get(DOWNLOAD_URL, headers=headers)
        if res.status_code == 200:
            with open(EXECUTAVEL, "wb") as f:
                f.write(res.content)
            messagebox.showinfo("Sucesso", "Script baixado com sucesso! Executando...")
            executar_e_apagar()
        else:
            messagebox.showerror("Erro", "Erro ao baixar o script.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro no download: {str(e)}")

def executar_e_apagar():
    try:
        # Executa o arquivo
        subprocess.Popen(EXECUTAVEL).wait()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao executar: {str(e)}")
    finally:
        # Remove o arquivo após execução
        try:
            os.remove(EXECUTAVEL)
        except:
            pass

def abrir_link():
    import webbrowser
    webbrowser.open(f"{API_URL}/recover-password")

# ----- GUI -----
janela = tk.Tk()
janela.title("DarkFov Loader")
janela.geometry("400x320")
janela.configure(bg="#0a0a0f")
janela.resizable(False, False)

# Centralizar janela
janela.eval('tk::PlaceWindow . center')

# Título
tk.Label(janela, text="DarkFov", fg="#00fff7", bg="#0a0a0f", font=("Orbitron", 24, "bold")).pack(pady=15)
tk.Label(janela, text="LOADER", fg="#ff00c8", bg="#0a0a0f", font=("Orbitron", 12)).pack(pady=(0, 20))

# Frame principal
frame = tk.Frame(janela, bg="#0a0a0f")
frame.pack(pady=10)

# Email
tk.Label(frame, text="Email", bg="#0a0a0f", fg="#e0e0e0", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=(0, 5))
entry_email = tk.Entry(frame, width=35, bg="#1a1a2e", fg="#e0e0e0", insertbackground="#00fff7", relief="flat", bd=5)
entry_email.grid(row=1, column=0, pady=(0, 15))

# Senha
tk.Label(frame, text="Senha", bg="#0a0a0f", fg="#e0e0e0", font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=(0, 5))
entry_senha = tk.Entry(frame, show="*", width=35, bg="#1a1a2e", fg="#e0e0e0", insertbackground="#00fff7", relief="flat", bd=5)
entry_senha.grid(row=3, column=0, pady=(0, 20))

# Botão de login
btn_login = tk.Button(janela, text="ENTRAR", bg="#00fff7", fg="#000", width=25, height=2, 
                     font=("Arial", 12, "bold"), relief="flat", cursor="hand2", command=login)
btn_login.pack(pady=10)

# Link de recuperação
recup = tk.Label(janela, text="Esqueci minha senha", fg="#ff00c8", bg="#0a0a0f", 
                cursor="hand2", font=("Arial", 9, "underline"))
recup.pack(pady=(10, 0))
recup.bind("<Button-1>", lambda e: abrir_link())

# Bind Enter para login
entry_email.bind("<Return>", lambda e: entry_senha.focus())
entry_senha.bind("<Return>", lambda e: login())

janela.mainloop()
