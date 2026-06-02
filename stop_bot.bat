@echo off
taskkill /F /FI "IMAGENAME eq pythonw.exe" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" 2>nul
echo Screen Solver Bot has been STOPPED.
timeout /t 3
