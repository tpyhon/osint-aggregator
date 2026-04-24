@echo off
cd /d C:\Users\takum\Desktop\code\osint-aggregator\crawler
call ..\venv\Scripts\activate.bat
python main.py
python cleanup.py
