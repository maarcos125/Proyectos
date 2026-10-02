@echo off
REM Ejecuta el Anotador de Imagenes (necesita Python instalado)
cd /d "%~dp0"
python -m pip install --quiet -r requirements.txt
start "" pythonw anotador.py %*
