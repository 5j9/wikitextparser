import sys
import cProfile

from wikitextparser import parse


with open('citation_template.txt', encoding='utf8') as f:
    text = f.read()

profiler = cProfile.Profile()

profiler.enable()
pprint_result = parse(text).pformat()
profiler.disable()

# copy(pprint_result)

with open('pp_profile_results.txt', 'w', encoding='utf8') as f:
    sys.stdout = f
    profiler.print_stats(sort='tottime')
