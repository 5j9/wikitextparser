#!/usr/bin/env bash
cd ../tests
coverage run __main__.py
coverage html
cd htmlcov
python -m webbrowser -t 'index.html'
