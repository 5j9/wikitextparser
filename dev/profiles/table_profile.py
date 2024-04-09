import cProfile
import sys

from wikitextparser import parse

with open('table_profile_input.txt', encoding='utf8') as f:
    text = f.read()

profiler = cProfile.Profile()

profiler.enable()
data = parse(text).tables[0].data()
profiler.disable()

# pp(parse_patern(text).tables[0].cells())

with open('table_profile_results.txt', 'w', encoding='utf8') as f:
    sys.stdout = f
    profiler.print_stats(sort='tottime')
