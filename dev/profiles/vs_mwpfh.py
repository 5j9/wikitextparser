import cProfile
from functools import partial
from timeit import repeat

import mwparserfromhell as mwp

import wikitextparser as wtp

# with open('vs_mwparserfromhell_input.txt', encoding='utf8') as f:
#     text = f.read()
#
#
# print('len(text):', len(text))

repeat = partial(
    repeat,
    number=1,
    repeat=10000,
    globals=globals())


def print_min(marker, statement):
    print(marker, min(repeat(statement)))


# Note that if the parse time is included, then wtp will be faster than mwp
p1 = wtp.parse("{{t|a|b|c|d}}")
print_min(
    'wtp,arg_val_assign',
    'p1.templates[0].arguments',
)  # 1.96000000000085e-05

p2 = mwp.parse("{{t|a|b|c|d}}")
print_min(
    'mwp,arg_val_assign',
    'p2.filter_templates()[0].params',
)  # 9.199999999986996e-06


assert p2.filter_templates()[0].params[3].name == p1.templates[0].arguments[3].name

profiler = cProfile.Profile()

# for i in range(10000):
#     p = wtp.parse("{{t|a}}")
#     profiler.enable()
#     p.templates[0].arguments[0].name
#     profiler.disable()
#
#
# with open('vs_mwpfh_results.txt', 'w', encoding='utf8') as f:
#     sys.stdout = f
#     profiler.print_stats(sort='tottime')
