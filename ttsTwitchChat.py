import socket
import pyttsx3
import re
import time
import threading
import keyboard
import os
import multiprocessing
import tkinter as tk
from dotenv import load_dotenv

load_dotenv()
# Configurações da Twitch xD
SERVER = "irc.chat.twitch.tv"
PORT = 6667
TOKEN = os.getenv("TOKEN")
USERNAME = os.getenv("USERNAME")
CHANNEL = os.getenv("CHANNEL")

# Inicializa o TTS
engine = pyttsx3.init()

# Variáveis globais para sincronização
stop_event = threading.Event()
stop_program = threading.Event()

# Dicionário para controle de envio por usuário
last_sent = {}

# Variáveis de configurações iniciais
settings = {
    "MAX_TTS_LENGTH": 200,
    "TTS_COMAND_LINE": "tts",
    "MINIMUN_TIME_BETWEEN_MESSAGES": 15
}

def sayFunc(phrase):
    """Função responsável por executar a fala."""
    engine.setProperty('rate', 160)  # Define a taxa de fala
    engine.say(phrase)
    engine.runAndWait()

def stop_speaking(p):
    """Interrompe o processo de fala atual."""
    print("Parando a fala...")
    p.terminate()  # Interrompe o processo de fala

def listen_for_stop_key(p):
    """Escuta o pressionamento de tecla para interromper o TTS."""
    keyboard.add_hotkey('q', stop_speaking, args=(p,))  # Interrompe o TTS quando 'q' é pressionado

def speak(text):
    """Inicia o processo de TTS."""
    p = multiprocessing.Process(target=sayFunc, args=(text,))
    p.start()

    # Inicia uma thread para escutar a tecla 'q' enquanto o TTS está sendo executado
    listen_for_stop_key(p)

    # Espera o processo de TTS terminar
    p.join()

def connect_to_twitch():
    """Conecta ao chat da Twitch."""
    sock = socket.socket()
    sock.connect((SERVER, PORT))
    sock.send(f"PASS {TOKEN}\n".encode("utf-8"))
    sock.send(f"NICK {USERNAME}\n".encode("utf-8"))
    sock.send(f"JOIN {CHANNEL}\n".encode("utf-8"))
    return sock

def extract_message(response):
    """Extrai usuário e mensagem do chat."""
    match = re.search(r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #[^:]+ :(.+)", response)
    if match:
        username = match.group(1)
        message = match.group(2)
        return username, message
    return None, None

def can_send_tts(username):
    """Verifica se o usuário pode enviar TTS novamente."""
    current_time = time.time()
    last_time = last_sent.get(username, 0)
    if current_time - last_time > 1:  # Intervalo de 15 segundos
        last_sent[username] = current_time
        return True
    return False

def read_messages(sock):
    """Lê mensagens do chat da Twitch."""
    while not stop_program.is_set():
        response = sock.recv(2048).decode("utf-8")
        if response.startswith("PING"):
            sock.send("PONG :tmi.twitch.tv\n".encode("utf-8"))
        else:
            username, message = extract_message(response)
            if username and message:
                print(f"{username}: {message}")
                tts_command = settings["TTS_COMAND_LINE"]
                max_length = settings["MAX_TTS_LENGTH"]

                if tts_command in message:
                    if can_send_tts(username):
                        clean_message = message.replace(tts_command, "").strip()
                        if not clean_message:
                            print(f"{username} enviou um comando TTS vazio.")
                            continue
                        if len(clean_message) > max_length:
                            clean_message = clean_message[:max_length] + "..."
                        speak(f"{username} disse {clean_message}")
                    else:
                        print(f"{username} tentou enviar TTS novamente muito rápido.")
                else:
                    print(f"Mensagem sem TTS: {message}")

def start_program():
    """Inicia o programa principal."""
    try:
        print(f"Conectando ao chat de {CHANNEL}...")        
        sock = connect_to_twitch()
        print(f"Conectado! Capturando mensagens...")

        read_messages(sock)
    except Exception as e:
        print(f"Erro no programa principal: {e}")

def open_settings():
    """Abre a interface para alterar configurações do TTS."""
    def save_settings():
        try:
            new_max_tts_length = int(max_tts_entry.get())
            new_tts_command_line = tts_command_entry.get().strip()
            new_time_between_message = int(minimum_time_entry.get())
            if new_max_tts_length > 0:
                settings["MAX_TTS_LENGTH"] = new_max_tts_length
            if new_tts_command_line:
                settings["TTS_COMAND_LINE"] = new_tts_command_line
            if new_time_between_message:
                settings["MINIMUN_TIME_BETWEEN_MESSAGES"] = new_time_between_message
            print(f"Configurações atualizadas: MAX_TTS_LENGTH={settings['MAX_TTS_LENGTH']}, TTS_COMAND_LINE='{settings['TTS_COMAND_LINE']}', MINIMUN_TIME_BETWEEN_MESSAGES='{settings['MINIMUN_TIME_BETWEEN_MESSAGES']}'")

            # Reinicia o programa principal
            stop_program.set()
            time.sleep(1)  # Aguarda para garantir o encerramento
            stop_program.clear()
            threading.Thread(target=start_program, daemon=True).start()
        except ValueError:
            print("Erro: MAX_TTS_LENGTH deve ser um número inteiro válido.")

    def exit_program():
        print("teste1")
        stop_program.set()
        root.destroy()

    root = tk.Tk()
    root.title("Configurações")

    tk.Label(root, text="Comprimento Máximo do TTS (MAX_TTS_LENGTH):").pack()
    max_tts_entry = tk.Entry(root)
    max_tts_entry.insert(0, str(settings["MAX_TTS_LENGTH"]))
    max_tts_entry.pack()

    tk.Label(root, text="Comando de TTS (TTS_COMAND_LINE):").pack()
    tts_command_entry = tk.Entry(root)
    tts_command_entry.insert(0, settings["TTS_COMAND_LINE"])
    tts_command_entry.pack()

    tk.Label(root, text="Comando de tempo minimo entre mensagens:").pack()
    minimum_time_entry = tk.Entry(root)
    minimum_time_entry.insert(0, settings["MINIMUN_TIME_BETWEEN_MESSAGES"])
    minimum_time_entry.pack()

    tk.Button(root, text="Salvar", command=save_settings).pack()
    tk.Label(root, text="Programa está sendo executado.").pack()
    tk.Button(root, text="Sair", command=exit_program).pack()

    root.mainloop()

if __name__ == "__main__":
    open_settings()
    start_program()
