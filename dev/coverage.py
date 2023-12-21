from subprocess import check_call
from webbrowser import open_new_tab

from pathlib import Path  # requires path
from os import chdir

repo = Path(__file__).parent.parent
chdir(repo)
check_call(['coverage', 'run', '-m', 'pytest'])
check_call(['coverage', 'html'])
open_new_tab(f'{repo}/htmlcov/index.html')
