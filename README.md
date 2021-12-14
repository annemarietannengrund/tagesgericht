# tagesgericht

# installation & setup

install [python 3.7+](https://www.python.org/downloads/)

```
coverage run -m unittest discover -s ./tests && coverage html
coverage run -m unittest discover ./tests --ignore=Sphinx-docs && coverage html
```
or
```
chmod +x *.sh
./tagesgericht.sh
```