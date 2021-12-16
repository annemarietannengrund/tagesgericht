%cd%\tagesgericht-venv\Scripts\python.exe "%cd%\main.py" "create_report"
call create_sphinx_report.bat
%SystemRoot%\explorer.exe "file:///%cd%\_build\html\index.html"