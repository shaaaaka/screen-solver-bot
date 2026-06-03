@echo off
cd /d "%~dp0"
start "" "%LocalAppData%\Python\pythoncore-3.14-64\pythonw.exe" main.py
echo Screen Solver Bot has been started SILENTLY in the background.
echo You can use your hotkey (Ctrl + Shift + F12) now.
timeout /t 3
