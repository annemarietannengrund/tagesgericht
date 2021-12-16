# tagesgericht

# installation & setup

install [python 3.7+](https://www.python.org/downloads/), make sure to check "add python 3.XX to Path".

also allow max pathlengths to be exceeded, at the end of the installer

then start the following bat file

setup.bat - prepare the virtual environment for this software

# run on windows

use the batchfiles.

create_html_report.bat - creates a html report and opens it in the browser

create_sphinx_report.bat - creates html report (internally used, nnot intended for you)

send_tagesgericht_tweet.bat - sends the prepared message for the day

stop_tagesgericht_tweet.bat - sends a sold-out message

check_code_coverage - creates a html code coverage ceport

# run on linux/mac

```
coverage run -m unittest discover -s ./tests && coverage html
coverage run -m unittest discover ./tests --ignore=Sphinx-docs && coverage html
```

or

```
chmod +x *.sh
./tagesgericht.sh
```

or

```
python main.py print_report
python main.py create_report
python main.py send_tweet
python main.py stoptweet
```