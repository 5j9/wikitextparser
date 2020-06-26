from subprocess import check_call
from webbrowser import open_new_tab

from path import Path  # requires path


repo = Path(__file__).parent.parent
repo.cd()
check_call(['coverage', 'run', '-m', 'pytest'])
check_call(['coverage', 'html'])
open_new_tab(repo / 'htmlcov/index.html')
