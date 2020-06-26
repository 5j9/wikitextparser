#!/usr/bin/env bash
from subprocess import check_call

from path import Path


wtp_dir = Path(__file__).parent.parent
wtp_dir.cd()
try:
    check_call(('python', 'setup.py', 'sdist', 'bdist_wheel'))
    check_call(('twine', 'upload', 'dist/*'))
finally:
    for d in ('dist', 'build', 'wikitextparser.egg-info'):
        (wtp_dir / d).rmtree()
