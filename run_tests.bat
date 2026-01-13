@echo off
chcp 65001 > nul
cd /d "%~dp0"
D:\ufukc\anaconda\python.exe -m pytest test_app.py -v --tb=short
pause

