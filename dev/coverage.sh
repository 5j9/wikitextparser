cd ../wikitextparser
coverage run wikitextparser_test.py
coverage html
read -n1 -r -p "Done!" key
