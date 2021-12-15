%cd%/tagesgericht-venv\Scripts\coverage.exe run -m unittest discover -s tests
%cd%/tagesgericht-venv\Scripts\coverage.exe html
%SystemRoot%\explorer.exe "file:///%cd%\htmlcov\index.html"