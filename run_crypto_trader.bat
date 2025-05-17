@echo off
echo Starting Crypto Trading Assistant...

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Run the application
python crypto_trader_gui.py

:: Deactivate virtual environment
call .venv\Scripts\deactivate.bat

pause 