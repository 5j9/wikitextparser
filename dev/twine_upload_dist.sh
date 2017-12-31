cd ..

echo Creating a Source Distribution:
python setup.py sdist
echo Creating a Pure Python Wheel:
python setup.py bdist_wheel

twine upload dist/*

rm -r dist build wikitextparser.egg-info

read -n1 -r -p 'Done!' key
