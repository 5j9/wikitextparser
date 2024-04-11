import cProfile
import sys

from wikitextparser import parse

with open('bold_italic_input.txt', encoding='utf8') as f:
    text = f.read()

profiler = cProfile.Profile()

profiler.enable()
plain_text = parse(text).plain_text()
profiler.disable()

with open('bold_italic_results.txt', 'w', encoding='utf8') as f:
    sys.stdout = f
    profiler.print_stats(sort='tottime')
