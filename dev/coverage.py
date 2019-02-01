from subprocess import check_call
from path import Path  # requires path.py

tests_dir = Path(__file__).parent.parent / 'tests'
tests_dir.cd()
check_call('coverage run __main__.py')
check_call('coverage html')
check_call('python -m webbrowser -t ' + (tests_dir / 'index.html'))
