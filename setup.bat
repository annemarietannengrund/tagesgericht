python -m venv %cd%\tagesgericht-venv
%cd%\tagesgericht-venv\Scripts\python.exe -m pip install --upgrade pip
%cd%\tagesgericht-venv\Scripts\python.exe -m pip install -r requirements.txt"
CALL create_html_report.bat