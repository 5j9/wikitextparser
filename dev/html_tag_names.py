from collections import Counter
from itertools import chain
from json import loads

from bs4 import BeautifulSoup
from regex import findall
from requests import get, post


def parse(text: str) -> str:
    return loads(
        post(
            'https://www.mediawiki.org/w/api.php',
            data={
                'action': 'parse',
                'text': text,
                'title': 'Test',
                'format': 'json',
                'formatversion': 2,
                'prop': 'text',
            },
        ).content
    )['parse']['text']


content = get(  # HTML elements reference
    'https://developer.mozilla.org/en-US/docs/Web/HTML/Element'
).content
soup = BeautifulSoup(content, features='lxml')
tds = soup.select('td a code')
counts = Counter(td.text.strip()[1:-1] for td in tds)
names = set(counts)

# 2020-04-20
# len(names) == 147
names_len = len(names)


self_ending_wikitext = ('#<{}\n/>\n' * names_len).format(*names)
start_only_wikitext = ('#<{}\n>\n' * names_len).format(*names)
end_only_wikitext = ('#</{}\n>\n' * names_len).format(*names)
start_and_end_wikitext = ('#<{}\n/></{}\n>\n' * names_len).format(
    *chain(*zip(names, names))
)

# https://www.mediawiki.org/wiki/API:Parsing_wikitext#Example_2:_Parse_a_section_of_a_page_and_fetch_its_table_data
self_ending_html = parse(self_ending_wikitext)
start_only_html = parse(start_only_wikitext)
end_only_html = parse(end_only_wikitext)
start_and_end_html = parse(start_and_end_wikitext)

invalid_self_ending_names = set(findall(r'(?<=&lt;)\w+', self_ending_html))
assert len(invalid_self_ending_names) == 86
valid_self_ending_names = names - invalid_self_ending_names

invalid_start_only_names = set(findall(r'(?<=&lt;)\w+', start_only_html))
assert len(invalid_start_only_names) == 88
valid_start_only_names = names - invalid_start_only_names

invalid_end_only_names = set(findall(r'(?<=&lt;/)\w+', end_only_html))
valid_end_only_names = names - invalid_end_only_names
assert valid_end_only_names == valid_start_only_names

invalid_start_and_end_names = set(findall(r'(?<=&lt;)\w+', start_and_end_html))
valid_start_and_end_names = names - invalid_start_and_end_names
assert valid_start_and_end_names == valid_self_ending_names

assert valid_self_ending_names - valid_start_only_names == {
    'section',
    'source',
}  # note that both of them are extension tags

# len(valid_start_only_names) == 59
print(valid_start_only_names)
# conclusion:
# valid_start_only_names == valid_end_only_names
# == valid_self_ending_names - extention_tags
# == {'s', 'code', 'blockquote', 'td', 'hr', 'h1', 'time', 'font', 'table',
# 'del', 'u', 'center', 'rtc', 'h4', 'h6', 'li', 'var', 'pre', 'wbr', 'rp',
# 'th', 'rt', 'h3', 'h2', 'ul', 'b', 'ruby', 'abbr', 'bdo', 'mark', 'sub',
# 'br', 'data', 'rb', 'strong', 'dfn', 'cite', 'q', 'tt', 'dd', 'ins', 'big',
# 'span', 'em', 'sup', 'div', 'h5', 'ol', 'bdi', 'kbd', 'dt', 'p', 'caption',
# 'samp', 'strike', 'small', 'dl', 'i', 'tr'}
# to be used in _config.py
