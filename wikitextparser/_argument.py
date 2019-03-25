"""Define the Argument class."""

from regex import compile as regex_compile, MULTILINE, DOTALL

from ._wikitext import SubWikiText, SECTION_HEADING
from ._spans import parse_to_spans

ARG_SHADOW_FULLMATCH = regex_compile(
    rb'[|:](?<pre_eq>(?:[^=]*+(?:' + SECTION_HEADING +
    rb'\n)?+)*+)(?:\Z|(?<eq>=)(?<post_eq>.*+))',
    MULTILINE | DOTALL).fullmatch


class Argument(SubWikiText):

    """Create a new Argument Object.

    Note that in MediaWiki documentation `arguments` are (also) called
    parameters. In this module the convention is:
    {{{parameter}}}, {{template|argument}}.
    See https://www.mediawiki.org/wiki/Help:Templates for more information.
    """

    @property
    def _shadow_match(self):
        cached_shadow_match, cache_string = getattr(
            self, '_shadow_match_cache', (None, None))
        self_string = str(self)
        if cache_string == self_string:
            return cached_shadow_match
        shadow_match = ARG_SHADOW_FULLMATCH(self._shadow)
        self._shadow_match_cache = shadow_match, self_string
        return shadow_match

    @property
    def name(self) -> str:
        """Return argument's name.

        For positional arguments return the position as a string.
        """
        lststr0 = self._lststr[0]
        ss = self._span[0]
        shadow_match = self._shadow_match
        if shadow_match['eq']:
            s, e = shadow_match.span('pre_eq')
            return lststr0[ss + s:ss + e]
        # positional argument
        position = 1
        # Todo: if we had the index of self._span, we could only look-up
        # the head of the self._type_to_spans.
        for s, e in self._type_to_spans[self._type]:
            if ss <= s:
                break
            arg_str = lststr0[s:e]
            if '=' in arg_str:
                # The argument may is still be positional if the equal sign is
                # inside an atomic sub-spans.
                byte_array = bytearray(arg_str, 'ascii', 'replace')
                parse_to_spans(byte_array)  # Remove sub-spans from byte_array
                if b'=' in byte_array:
                    # This is a keyword argument.
                    continue
            # This is a preceding positional argument.
            position += 1
        return str(position)

    @name.setter
    def name(self, newname: str) -> None:
        """Set the name for this argument.

        If this is a positional argument, convert it to keyword argument.
        """
        oldname = self.name
        if self._shadow_match['eq']:
            self[1:1 + len(oldname)] = newname
        else:
            self[0:1] = '|' + newname + '='

    @property
    def positional(self) -> bool:
        """Return True if there is an equal sign in the argument else False."""
        return False if self._shadow_match['eq'] else True

    @positional.setter
    def positional(self, to_positional: bool) -> None:
        """Change to keyword or positional accordingly.

        Raise ValueError on trying to convert positional to keyword argument.
        """
        shadow_match = self._shadow_match
        if shadow_match['eq']:
            # Keyword argument
            if to_positional:
                del self[1:shadow_match.end('eq')]
            else:
                return
        if to_positional:
            # Positional argument. to_positional is True.
            return
        # Positional argument. to_positional is False.
        raise ValueError(
            'Converting positional argument to keyword argument is not '
            'possible without knowing the new name. '
            'You can use `self.name = somename` instead.')

    @property
    def value(self) -> str:
        """Return value of a keyword argument."""
        shadow_match = self._shadow_match
        if shadow_match['eq']:
            return self[shadow_match.start('post_eq'):]
        return self[1:]

    @value.setter
    def value(self, newvalue: str) -> None:
        """Assign the newvalue to self."""
        shadow_match = self._shadow_match
        if shadow_match['eq']:
            self[shadow_match.start('post_eq'):] = newvalue
        else:
            self[1:] = newvalue

    @property
    def _lists_shadow_ss(self):
        shadow_match = self._shadow_match
        if shadow_match['eq']:
            post_eq = shadow_match['post_eq']
            ls_post_eq = post_eq.lstrip()
            return (
                ls_post_eq,
                self._span[0] + shadow_match.start('post_eq')
                + len(post_eq) - len(ls_post_eq))
        return shadow_match[0][1:], self._span[0] + 1
