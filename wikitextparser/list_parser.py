import re


class MWException(RuntimeError):
    """Throw new MWException."""

    pass


class ListParser:
    """Parse ordered/unordere/definition lists in wikitext."""

    PRE_CLOSE_REGEX = re.compile(r'</pre', re.IGNORECASE)
    PRE_OPEN_REGEX = re.compile(r'<pre', re.IGNORECASE)
    # Prefix and suffix for temporary replacement strings
    # for the multipass parser.
    # \x7f should never appear in input as it's disallowed in XML.
    # Using it at the front also gives us a little extra robustness
    # since it shouldn't match when butted up against identifier-like
    # string constructs.
    # Must not consist of all title characters, or else it will change
    # the behavior of <nowiki> in a link.
    MARKER_SUFFIX = "-QINU\x7f"
    MARKER_PREFIX = "\x7fUNIQ-"
    OPEN_MATCH_REGEX = re.compile(
        r'(?:<table|<h1|<h2|<h3|<h4|<h5|<h6|<pre|<tr|'
        r'<p|<ul|<ol|<dl|<li|</tr|</td|</th)',
        re.IGNORECASE
    )
    CLOSE_MATCH_REGEX = re.compile(
        r'(?:</table|</h1|</h2|</h3|</h4|</h5|</h6|'
        r'<td|<th|</?blockquote|</?div|<hr|</pre|</p|</mw:|' +
        MARKER_PREFIX + r'-pre|</li|</ul|</ol|</dl|</?center)',
        re.IGNORECASE
    )
    BLOCKQUOTE_REGEX = re.compile('<(/?)blockquote[\s>]', re.IGNORECASE)
    # State constants for the definition list colon extraction
    COLON_STATE_TEXT = 0
    COLON_STATE_TAG = 1
    COLON_STATE_TAGSTART = 2
    COLON_STATE_CLOSETAG = 3
    COLON_STATE_TAGSLASH = 4
    COLON_STATE_COMMENT = 5
    COLON_STATE_COMMENTDASH = 6
    COLON_STATE_COMMENTDASHDASH = 7

    def __init__(self):
        """Initialize the instance."""
        self.m_in_pre = False
        self.m_last_section = ''

    def do_block_levels(self, text, linestart):
        """Make lists from lines starting with ':', '*', '#', etc.

        `text` is a string to be parsed.
        `linestart` is a bool value that indicates whether or not the text is a
            t the start of a line.

        Return the text with lists rendered in as HTML.

        This is function is a line by line conversion of MW's
            parser.php::doBlockLevels into Python. See [1].

        [1]: https://github.com/wikimedia/mediawiki/blob/220e11d65165aee4724a043fa0e0f27083f5865a/includes/parser/Parser.php#L2534

        """
        # Parsing through the text line by line.  The main thing
        # happening here is handling of block-level elements p, pre,
        # and making lists from lines starting with * # : etc.
        text_lines = text.split('\n')

        last_prefix = output = ''
        self.m_dt_open = in_block_elem = False
        prefix_length = 0
        paragraph_stack = False
        in_blockquote = False

        for oline in text_lines:
            # Fix up linestart
            if not linestart:
                output += oline
                linestart = True
                continue
            # * = ul
            # # = ol
            # ; = dt
            # : = dd

            last_prefix_length = len(last_prefix)
            pre_close_match = self.PRE_CLOSE_REGEX.search(oline)
            pre_open_match = self.PRE_OPEN_REGEX.search(oline)
            # If not in a <pre> element, scan for and figure out what prefixes
            # are there.
            if not self.m_in_pre:
                # Multiple prefixes may abut each other for nested lists.
                prefix_length = _strspn(oline, '*#:;')
                prefix = oline[:prefix_length]

                # eh?
                # ; and : are both from definition-lists, so they're
                # equivalent for the purposes of determining whether or not
                # we need to open/close elements.
                prefix2 = prefix.replace(';', ':')
                t = oline[prefix_length:]
                self.m_in_pre = bool(pre_open_match)
            else:
                # Don't interpret any other prefixes in preformatted text.
                prefix_length = 0
                prefix = prefix2 = ''
                t = oline

            # List generation
            if prefix_length and last_prefix == prefix2:
                # Same as the last item, so no need to deal with
                # nesting or opening stuff.
                output += self.next_item(prefix[-1])
                paragraph_stack = False

                if prefix[-1] == ';':
                    # The one nasty exception: definition lists work like this:
                    # ; title : definition text
                    # So we check for : in the remainder text to split up the
                    # title and definition, without b0rking links.
                    term = t2 = ''
                    found_colon, term, t2 = self.find_colon_no_links(t)
                    if found_colon is not False:
                        t = t2
                        output += term + self.next_item(':')

            elif prefix_length or last_prefix_length:
                # We need to open or close prefixes, or both.

                # Either open or close a level...
                common_prefix_length = self.get_common(prefix, last_prefix)
                paragraph_stack = False

                # Close all the prefixes which aren't shared.
                while common_prefix_length < last_prefix_length:
                    output += self.close_list(
                        last_prefix[last_prefix_length - 1]
                    )
                    last_prefix_length -= 1
                # Continue the current prefix if appropriate.
                if (
                    prefix_length <= common_prefix_length and
                    common_prefix_length > 0
                ):
                    output += self.next_item(prefix[common_prefix_length - 1])

                # Open prefixes where appropriate.
                if last_prefix and prefix_length > common_prefix_length:
                    output += '\n'

                while prefix_length > common_prefix_length:
                    char = prefix[common_prefix_length]
                    output += self.open_list(char)

                    if char == ';':
                        # FIXME: This is dupe of code above
                        found_colon, term, t2 = self.find_colon_no_links(t)
                        if found_colon is not False:
                            t = t2
                            output += term + self.next_item(':')

                    common_prefix_length += 1

                if not prefix_length and last_prefix:
                    output += '\n'
                last_prefix = prefix2

            # If we have no prefixes, go to paragraph mode.
            if prefix_length == 0:
                # No prefix (not in list)--go to paragraph mode
                # XXX: use a stack for nestable elements like
                #    span, table and div
                openmatch = self.OPEN_MATCH_REGEX.search(t)
                closematch = self.CLOSE_MATCH_REGEX.search(t)
                if openmatch or closematch:
                    paragraph_stack = False
                    # @todo bug 5718: paragraph closed
                    output += self.close_paragraph()
                    if pre_open_match and not pre_close_match:
                        self.m_in_pre = True
                    for bq_match in self.BLOCKQUOTE_REGEX.finditer(t):
                        # Is this a close tag?
                        self.in_blockquote = not bq_match.group(1)
                    in_block_elem = not closematch

                elif not in_block_elem and not self.m_in_pre:
                    if t[0] == ' ' and (
                            self.m_last_section == 'pre' or t.strip() != ''
                    ) and not in_blockquote:
                        # pre
                        if self.m_last_section != 'pre':
                            paragraph_stack = False
                            output += self.close_paragraph() + '<pre>'
                            self.m_last_section = 'pre'
                        t = t[1:]
                    else:
                        # paragraph
                        if t.strip() == '':
                            if paragraph_stack:
                                output += paragraph_stack + '<br />'
                                paragraph_stack = False
                                self.m_last_section = 'p'
                            else:
                                if self.m_last_section != 'p':
                                    output += self.close_paragraph()
                                    self.m_last_section = ''
                                    paragraph_stack = '<p>'
                                else:
                                    paragraph_stack = '</p><p>'
                        else:
                            if paragraph_stack:
                                output += paragraph_stack
                                paragraph_stack = False
                                self.m_last_section = 'p'
                            elif self.m_last_section != 'p':
                                output += self.close_paragraph() + '<p>'
                                self.m_last_section = 'p'

            # somewhere above we forget to get out of pre block (bug 785)
            if pre_close_match and self.m_in_pre:
                self.m_in_pre = False

            if not paragraph_stack:
                output += t
                if prefix_length == 0:
                    output += '\n'

        while prefix_length:
            output += self.close_list(prefix2[prefix_length - 1])
            prefix_length -= 1
            if not prefix_length:
                output += '\n'

        if self.m_last_section != '':
            output += '</' + self.m_last_section + '>'
            self.m_last_section = ''

        return output

    def get_common(self, st1: str, st2: str):
        """Return the length of the longest common substring."""
        fl = len(st1)
        shorter = len(st2)
        if fl < shorter:
            shorter = fl

        i = 0
        while i < shorter:
            if st1[i] != st2[i]:
                break
            i += 1
        return i

    def open_list(self, char: str) -> str:
        """Open the list element if the prefix char requires so."""
        result = self.close_paragraph()

        if char == '*':
            result += '<ul><li>'
        elif char == '#':
            result += '<ol><li>'
        elif char == ':':
            result += '<dl><dd>'
        elif char == ';':
            result += '<dl><dt>'
            self.m_dt_open = True
        else:
            result += '<!-- ERR 1 -->'

        return result

    def close_paragraph(self) -> str:
        """Used by doBlockLevels()."""
        result = ''
        if self.m_last_section:
            result = '</' + self.m_last_section + '>\n'
        self.m_in_pre = False
        self.m_last_section = ''
        return result

    def close_list(self, char: str) -> str:
        """Close the list element if the prefix char requires so.

        Parser::closeList.

        """
        if char == '*':
            text = '</li></ul>'
        elif char == '#':
            text = '</li></ol>'
        elif char == ':':
            if self.m_dt_open:
                self.m_dt_open = False
                text = '</dt></dl>'
            else:
                text = '</dd></dl>'
        else:
            return '<!-- ERR 3 -->'
        return text

    def next_item(self, char: str) -> str:
        """Continue the list element if the prefix char requires so.

        Equivalent to MW's parser::nextItem.

        """
        if char == '*' or char == '#':
            return '</li>\n<li>'
        elif char == ':' or char == ';':
            close = '</dd>\n'
            if self.m_dt_open:
                close = '</dt>\n'
            if char == ';':
                self.m_dt_open = True
                return close + '<dt>'
            else:
                self.m_dt_open = False
                return close + '<dd>'
        return '<!-- ERR 2 -->'

    def find_colon_no_links(self, string: str) -> (int or False, str, str):
        """Split up a string on ':'. Return (position, before, after).

        Ignore any occurrences inside tags to prevent illegal overlapping.

        `string` is the string to split.

        Return (position, before, after) where
            `position` is the position of the ':', or false if none found.
            `before` is everything before the ':'.
            `after` is everything after the ':'.

        This function may raise MWException.

        The actual function signature in MW is
            findColonNoLinks( $str, &$before, &$after )
        Unlike PHP, Python's strings are immutable, so as workaround, here
        those parameter are returned as the result.

        """
        pos = string.find(':')
        if pos == -1:
            # Nothing to find!
            return False, '', ''
        lt = string.find('<')
        if lt == -1 or lt > pos:
            # Easy; no tag nesting to worry about
            before = string[:pos]
            after = string[pos + 1:]
            return pos, before, after

        # Ugly state machine to walk through avoiding tags.
        state = self.COLON_STATE_TEXT
        stack = 0
        # len_ = len(string)
        for i, c in enumerate(string):
            # (Using the number is a performance hack for common cases)
            if state == 0:  # self.COLON_STATE_TEXT:
                if c == "<":
                    # Could be either a <start> tag or an </end> tag
                    state = self.COLON_STATE_TAGSTART
                elif c == ":":
                    if stack == 0:
                        # We found it!
                        before = string[:i]
                        after = string[i + 1:]
                        return i, before, after
                    # Embedded in a tag; don't break it.
                else:
                    # Skip ahead looking for something interesting
                    colon = string.find(':', start=i)
                    if colon == -1:
                        # Nothing else interesting
                        return False, '', ''
                    lt = string.find('<', start=i)
                    if stack == 0:
                        if lt == -1 or colon < lt:
                            # We found it!
                            before = string[:colon]
                            after = string[colon + 1:]
                            return i, before, after
                    if lt == -1:
                        # Nothing else interesting to find; abort!
                        # We're nested, but there's no close tags left. Abort!
                        # break 2 (c and state)
                        pass
                    else:
                        # Skip ahead to next tag start
                        i = lt
                        state = self.COLON_STATE_TAGSTART
            elif state == 1:  # self.COLON_STATE_TAG:
                # In a <tag>
                if c == ">":
                    stack += 1
                    state = self.COLON_STATE_TEXT
                elif c == "/":
                    # Slash may be followed by >?
                    state = self.COLON_STATE_TAGSLASH
                else:
                    # ignore
                    pass
            elif state == 2:  # self.COLON_STATE_TAGSTART:
                if c == "/":
                    state = self.COLON_STATE_CLOSETAG
                elif c == '!':
                    state = self.COLON_STATE_COMMENT
                elif c == ">":
                    # Illegal early close? This shouldn't happen D:
                    state = self.COLON_STATE_TEXT
                else:
                    state = self.COLON_STATE_TAG
            elif state == 3:  # self.COLON_STATE_CLOSETAG:
                # In a </tag>
                if c == ">":
                    stack -= 1
                    if stack < 0:
                        # wfDebug: Invalid input; too many close tags.
                        return False, '', ''
                    else:
                        state = self.COLON_STATE_TEXT
            elif state == self.COLON_STATE_TAGSLASH:
                if c == ">":
                    # Yes, a self-closed tag <blah/>
                    state = self.COLON_STATE_TEXT
                else:
                    # Probably we're jumping the gun, and this is an attribute
                    state = self.COLON_STATE_TAG
            elif state == 5:  # self.COLON_STATE_COMMENT:
                if c == "-":
                    state = self.COLON_STATE_COMMENTDASH
            elif state == self.COLON_STATE_COMMENTDASH:
                if c == "-":
                    state = self.COLON_STATE_COMMENTDASHDASH
                else:
                    state = self.COLON_STATE_COMMENT
            elif state == self.COLON_STATE_COMMENTDASHDASH:
                if c == ">":
                    state = self.COLON_STATE_TEXT
                else:
                    state = self.COLON_STATE_COMMENT
            else:
                raise MWException('State machine error')
        if stack > 0:
            # wfDebug: Invalid input; not enough close tags
            return False, '', ''
        return False, '', ''


def _strspn(string: str, mask: str) -> int:
    """Find length of initial segment matching mask.

    Replacement for PHP's strspn (without the last two args).

    """
    return len(re.match(r'[' + re.escape(mask) + r']*', string).group(0))
