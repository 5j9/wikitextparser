#!/usr/bin/env bash
cd ..

python setup.py sdist
python setup.py bdist_wheel
twine upload dist/*
rm -r dist build wikitextparser.egg-info

read -n1 -r -p 'Done!' key
