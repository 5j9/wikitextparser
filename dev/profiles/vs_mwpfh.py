import sys
from timeit import timeit
import cProfile

import wikitextparser as wtp
import mwparserfromhell as mwp


# with open('vs_mwparserfromhell_input.txt', encoding='utf8') as f:
#     text = f.read()
#
#
# print('len(text):', len(text))


# Template manipulation

# Note that if the parse time is included, then wtp will be faster than mwp
print('wtp,arg_val_assign', timeit(
    'p.templates[0].arguments[3].value = "50"',
    'p = wtp.parse("{{t|a|b|c|d}}")',
    number=10**4,
    globals=globals()
))  # 0.5908590695883216


p = mwp.parse("{{t|a|b|c|d}}")
p.filter_templates()[0].params[3].value = "50"
print('mwp,arg_val_assign', timeit(
    'p.filter_templates()[0].params[3].value = "50"',
    'p = mwp.parse("{{t|a|b|c|d}}")',
    number=10**4,
    globals=globals()
))  # 0.21268005219747488

# profiler = cProfile.Profile()
#
# for i in range(10000):
#     p = wtp.parse("{{t|a}}")
#     profiler.enable()
#     p.templates[0].arguments[0].value = "50"
#     profiler.disable()
#
#
# with open('vs_mwpfh_results.txt', 'w', encoding='utf8') as f:
#     sys.stdout = f
#     profiler.print_stats(sort='tottime')


# todo: add test for tag extraction comparison
