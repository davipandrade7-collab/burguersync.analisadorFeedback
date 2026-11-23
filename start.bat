@echo off
setlocal
echo [INFO] Iniciando BurgerSync Feedback Analyzer...
set "PYTHON_EXE=C:\Users\Aluno\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)
"%PYTHON_EXE%" execution\server.py
pause
