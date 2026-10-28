@echo off
title AetherDeck - Installation des Moteurs d'Emulation
cd /d "%~dp0"
echo ====================================================================
echo   AetherDeck - Installation des dependances Python et des 16 moteurs
echo ====================================================================
python -m pip install -r requirements.txt
python -m playwright install chromium
python setup_engines.py
pause
