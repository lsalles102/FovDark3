
import tkinter as tk
from tkinter import messagebox
import requests
import subprocess
import os
import json

# URL do seu projeto atual
API_URL = "https://replit.com/@seunome/seuprojetorepl"  # Substitua pela URL correta
LOGIN_URL = f"{API_URL}/api/login"
LICENSE_URL = f"{API_URL}/api/license/check"
DOWNLOAD_URL = f"{API_URL}/api/download/executable"
EXECUTAVEL = "Script_Dark.exe"
CONFIG_FILE = "darkfov_config.json"

def carregar_credenciais():
    """Carrega credenciais salvas se existirem"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                if config.get("salvar_login", False):
                    entry_email.insert(0, config.get("email", ""))
                    entry_senha.insert(0, config.get("senha", ""))
                    var_salvar.set(True)
    except Exception:
        pass

def salvar_credenciais(email, senha, salvar):
    """Salva ou remove credenciais baseado na checkbox"""
    try:
        config = {}
        if salvar:
            config = {
                "email": email,
                "senha": senha,
                "salvar_login": True
            }
        else:
            config = {"salvar_login": False}
            
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception:
        pass

def login():
    email = entry_email.get()
    senha = entry_senha.get()
    
    if not email or not senha:
        messagebox.showwarning("Campos obrigatórios", "Preencha email e senha.")
        return

    # Salvar credenciais se solicitado
    salvar_credenciais(email, senha, var_salvar.get())

    # Mostrar loading
    btn_login.config(text="CONECTANDO...", state="disabled")
    janela.update()

    try:
        # Login usando Form data conforme o sistema atual
        data = {"email": email, "password": senha}
        res = requests.post(LOGIN_URL, data=data, timeout=10)
        
        if res.status_code != 200:
            error_msg = "Login inválido."
            try:
                error_data = res.json()
                error_msg = error_data.get("detail", error_msg)
            except:
                pass
            messagebox.showerror("Erro", error_msg)
            return
            
        token = res.json()["access_token"]
    except requests.exceptions.Timeout:
        messagebox.showerror("Erro", "Timeout na conexão. Verifique sua internet.")
        return
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Erro", "Não foi possível conectar ao servidor. Verifique se a URL está correta.")
        return
    except Exception as e:
        messagebox.showerror("Erro", f"Falha na conexão: {str(e)}")
        return

    # Verifica licença
    headers = {"Authorization": f"Bearer {token}"}
    try:
        lic = requests.get(LICENSE_URL, headers=headers, timeout=10)
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
        btn_login.config(text="BAIXANDO...")
        janela.update()
        
        res = requests.get(DOWNLOAD_URL, headers=headers, timeout=30)
        if res.status_code == 200:
            with open(EXECUTAVEL, "wb") as f:
                f.write(res.content)
            messagebox.showinfo("Sucesso", "Script baixado com sucesso! Executando...")
            executar_e_apagar()
        else:
            messagebox.showerror("Erro", "Erro ao baixar o script.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro no download: {str(e)}")
    finally:
        btn_login.config(text="ENTRAR", state="normal")

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

def abrir_recuperacao():
    import webbrowser
    webbrowser.open(f"{API_URL}/recover-password")

def testar_conexao():
    """Função para testar a conexão com o servidor"""
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            messagebox.showinfo("Teste", "Conexão com servidor OK!")
        else:
            messagebox.showwarning("Teste", f"Servidor respondeu com código: {response.status_code}")
    except Exception as e:
        messagebox.showerror("Teste", f"Erro na conexão: {str(e)}")

# ----- GUI -----
janela = tk.Tk()
janela.title("DarkFov Loader")
janela.geometry("400x380")
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
entry_senha.grid(row=3, column=0, pady=(0, 15))

# Checkbox salvar login
var_salvar = tk.BooleanVar()
check_salvar = tk.Checkbutton(frame, text="Salvar login", variable=var_salvar, 
                             bg="#0a0a0f", fg="#e0e0e0", selectcolor="#1a1a2e", 
                             activebackground="#0a0a0f", activeforeground="#00fff7",
                             font=("Arial", 9))
check_salvar.grid(row=4, column=0, sticky="w", pady=(0, 20))

# Botão de login
btn_login = tk.Button(janela, text="ENTRAR", bg="#00fff7", fg="#000", width=25, height=2, 
                     font=("Arial", 12, "bold"), relief="flat", cursor="hand2", command=login)
btn_login.pack(pady=10)

# Botão de teste (para debug)
btn_teste = tk.Button(janela, text="TESTAR CONEXÃO", bg="#ff00c8", fg="#000", width=25, height=1, 
                     font=("Arial", 10), relief="flat", cursor="hand2", command=testar_conexao)
btn_teste.pack(pady=5)

# Link de recuperação
recup = tk.Label(janela, text="Esqueci minha senha", fg="#ff00c8", bg="#0a0a0f", 
                cursor="hand2", font=("Arial", 9, "underline"))
recup.pack(pady=(10, 0))
recup.bind("<Button-1>", lambda e: abrir_recuperacao())

# Carregar credenciais salvas
carregar_credenciais()

# Bind Enter para login
entry_email.bind("<Return>", lambda e: entry_senha.focus())
entry_senha.bind("<Return>", lambda e: login())

janela.mainloop()
