#!/usr/bin/env bash
from subprocess import check_call
from path import Path  # requires path.py

wtp_dir = Path(__file__).parent.parent
wtp_dir.cd()
check_call('python setup.py sdist')
check_call('python setup.py bdist_wheel')
check_call('twine upload dist/*')
for d in ('dist', 'build', 'wikitextparser.egg-info'):
    (wtp_dir / d).rmtree()
input('Done! Press Enter to exit.')
