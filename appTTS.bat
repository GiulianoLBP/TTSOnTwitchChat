@echo off
REM Muda para o diretório onde está o script
cd /d "C:\Twitch"

REM Ativa o ambiente Anaconda
call "C:\Users\giuli\anaconda3\Scripts\activate.bat" base

REM Executa o script Python
"C:\Users\giuli\anaconda3\python.exe" "C:\Twitch\xicara_tts.py"

REM Mantém o terminal aberto após execução
pause
