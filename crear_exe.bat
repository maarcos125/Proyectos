@echo off
REM Crea dist\AnotadorImagenes.exe (un unico archivo, no necesita Python para usarlo)
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name AnotadorImagenes anotador.py
echo.
echo Listo: dist\AnotadorImagenes.exe
pause
