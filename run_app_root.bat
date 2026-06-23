@echo off
cd /d "%~dp0"
"%~dp0\.venv\Scripts\python.exe" -m streamlit run "multilingual-RAG-system--main\app.py"
pause

