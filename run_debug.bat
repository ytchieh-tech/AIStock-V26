@echo off
cd /d "%~dp0"
python -m py_compile app.py
if errorlevel 1 pause
python -m streamlit run app.py --server.port 8518 --server.address 0.0.0.0
pause
