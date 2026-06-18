@echo off
cd /d "%~dp0"
title Run V25 Mobile Professional
echo Running V25 Mobile Professional on http://localhost:8518
echo.
echo Phone URL will be shown as Network URL after startup.
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8518 --server.address 0.0.0.0
pause
