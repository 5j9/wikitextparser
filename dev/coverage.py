from subprocess import check_call
from path import Path  # requires path.py
from webbrowser import open_new_tab

repo = Path(__file__).parent.parent
repo.cd()
check_call(['coverage', 'run', 'tests'])
check_call(['coverage', 'html'])
open_new_tab(repo / 'htmlcov/index.html')
