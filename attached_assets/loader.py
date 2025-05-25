import tkinter as tk
from tkinter import messagebox
import requests
import subprocess
import os

API_URL = "https://seuprojeto.up.railway.app"
LOGIN_URL = f"{API_URL}/login"
LICENSE_URL = f"{API_URL}/license/check"
DOWNLOAD_URL = f"{API_URL}/download"
EXECUTAVEL = "dark_script.exe"

def login():
    email = entry_email.get()
    senha = entry_senha.get()
    
    if not email or not senha:
        messagebox.showwarning("Campos obrigatórios", "Preencha email e senha.")
        return

    try:
        res = requests.post(LOGIN_URL, json={"email": email, "password": senha})
        if res.status_code != 200:
            messagebox.showerror("Erro", "Login inválido.")
            return
        token = res.json()["access_token"]
    except:
        messagebox.showerror("Erro", "Falha na conexão com o servidor.")
        return

    # Verifica licença
    headers = {"Authorization": f"Bearer {token}"}
    lic = requests.get(LICENSE_URL, headers=headers)
    if lic.status_code != 200:
        messagebox.showwarning("Licença inválida", "Sua licença está expirada ou inválida.")
        return

    # Baixa o executável
    res = requests.get(DOWNLOAD_URL, headers=headers)
    if res.status_code == 200:
        with open(EXECUTAVEL, "wb") as f:
            f.write(res.content)
        executar_e_apagar()
    else:
        messagebox.showerror("Erro", "Erro ao baixar o script.")

def executar_e_apagar():
    try:
        subprocess.Popen(EXECUTAVEL).wait()
    finally:
        os.remove(EXECUTAVEL)

def abrir_link():
    import webbrowser
    webbrowser.open("https://seusite.com/recuperar-senha")

# ----- GUI -----
janela = tk.Tk()
janela.title("DarkFov Loader")
janela.geometry("350x280")
janela.configure(bg="#0a0a0f")

tk.Label(janela, text="DarkFov", fg="#00fff7", bg="#0a0a0f", font=("Orbitron", 20)).pack(pady=10)

frame = tk.Frame(janela, bg="#0a0a0f")
frame.pack(pady=10)

tk.Label(frame, text="Email", bg="#0a0a0f", fg="#e0e0e0").grid(row=0, column=0, sticky="w")
entry_email = tk.Entry(frame, width=30)
entry_email.grid(row=1, column=0, pady=5)

tk.Label(frame, text="Senha", bg="#0a0a0f", fg="#e0e0e0").grid(row=2, column=0, sticky="w")
entry_senha = tk.Entry(frame, show="*", width=30)
entry_senha.grid(row=3, column=0, pady=5)

btn_login = tk.Button(janela, text="Entrar", bg="#00fff7", fg="#000", width=20, command=login)
btn_login.pack(pady=10)

recup = tk.Label(janela, text="Esqueci minha senha", fg="#ff00c8", bg="#0a0a0f", cursor="hand2")
recup.pack()
recup.bind("<Button-1>", lambda e: abrir_link())

janela.mainloop()
