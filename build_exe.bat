@echo off
cd /d "%~dp0"
title Build V25 Mobile Professional EXE
echo ============================================
echo Build Flagship AI Stock Platform V25 MOBILE PRO
echo ============================================
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
python -m PyInstaller ^
--onefile ^
--noconfirm ^
--clean ^
--name Flagship_AI_Stock_Platform_V25_MOBILE_PRO ^
--add-data "app.py;." ^
--collect-all streamlit ^
--collect-all plotly ^
--collect-all pandas ^
--collect-all numpy ^
--collect-all yfinance ^
--collect-all sklearn ^
--collect-all xgboost ^
launcher.py
echo.
echo DONE
echo EXE:
echo %cd%\dist\Flagship_AI_Stock_Platform_V25_MOBILE_PRO.exe
pause
