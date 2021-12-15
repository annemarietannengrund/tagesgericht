#!/bin/zsh

python main.py
cd Sphinx-docs && make html && cd .. && open Sphinx-docs/_build/html/index.html