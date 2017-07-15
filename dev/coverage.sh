#!/usr/bin/env bash
cd ../wikitextparser
coverage run wikitextparser_test.py
coverage html
cd htmlcov
python -m webbrowser -t 'index.html'
