"""All independant methods of Wikitext class are defined here."""


import re


class WikiText:

    """Define the independant methods of the WikiText class."""

    def __str__(self):
        """Return self-object as a string."""
        return self.string


    def __repr__(self):
        """Return the string representation of the WikiText."""
        return 'WikiText(' + repr(self.string) + ')'

    def __contains__(self, parsed_wikitext):
        """Return True if parsed_wikitext is inside self. False otherwise.

        Also self and parsed_wikitext should belong to the same parsed
        wikitext object for this function to return True.
        """
        # Is it usefull (and a good practice) to also accepts str inputs
        # and check if self.string contains it?
        if self._lststr is not parsed_wikitext._lststr:
            return False
        ps, pe = parsed_wikitext._get_span()
        ss, se = self._get_span()
        if ss <= ps and se >= pe:
            return True
        return False
            
    @property
    def string(self):
        """Retrun str(self)."""
        start, end = self._get_span()
        return self._lststr[0][start:end]

    @string.setter
    def string(self, newstring):
        """Set a new string for this object. Update spans accordingly.

        This method can be slow because it uses SequenceMatcher to
        find-out the exact position of each change occured in the
        newstring.

        It tries to avoid the SequenceMatcher by checking to see if the
        newnewstring is a simple concatination at the start or end of the
        oldstring. For long strings, it's highly recommended to use this
        feature and avoid inserting in the middle of the string.
        """
        lststr = self._lststr
        lststr0 = lststr[0]
        oldstart, oldend = self._get_span()
        oldstring = lststr0[oldstart:oldend]
        # Updating lststr
        lststr[0] = lststr0[:oldstart] + newstring + lststr0[oldend:]
        # Updating spans
        oldlength = oldend - oldstart
        newlength = len(newstring)
        if oldlength == newlength:
            if newstring == oldstring:
                return
        elif oldlength < newlength:
            if newstring.startswith(oldstring):
                # The has been an insertion at the end of oldstring.
                self._extend_span_update(
                    estart=oldstart + oldlength,
                    elength=newlength - oldlength,
                )
                return
            if newstring.endswith(oldstring):
                # The has been an insertion at the beggining of oldstring.
                self._extend_span_update(
                    estart=oldstart,
                    elength=newlength - oldlength,
                )
                return
        else: # oldlength > newlength
            if oldstring.startswith(newstring):
                # The ending part of oldstring has been deleted.
                self._shrink_span_update(
                    rmstart=oldstart + newlength,
                    rmend=oldstart + oldlength,
                )
                return
            if oldstring.endswith(newstring):
                # The starting part of oldstring has been deleted.
                self._shrink_span_update(
                    rmstart=oldstart,
                    rmend=oldstart + oldlength - newlength,
                )
                return
        sm = SequenceMatcher(None, oldstring, newstring, autojunk=False)
        opcodes = [oc for oc in sm.get_opcodes() if oc[0] != 'equal']
        # Opcodes also need adjustment as the spans change.
        opcodes_spans = [
            (oldstart + i, oldstart + j)
            for o in opcodes
            for i in o[1::4] for j in o[2::4]
        ]
        self._spans['opcodes'] = opcodes_spans
        for tag, i1, i2, j1, j2 in opcodes:
            i1, i2 = opcodes_spans.pop(0)
            i1 -= oldstart
            i2 -= oldstart
            if tag == 'replace':
                # a[i1:i2] should be replaced by b[j1:j2].
                len1 = i2 - i1
                len2 = j2 - j1
                if len2 < len1:
                    self._shrink_span_update(
                        rmstart=oldstart + i1 + len2,
                        rmend=oldstart + i2,
                    )
                elif len2 > len1:
                    self._extend_span_update(
                        estart=oldstart + i2,
                        elength=len2 - len1,
                    )
            elif tag == 'delete':
                # a[i1:i2] should be deleted.
                # Note that j1 == j2 in this case.
                self._shrink_span_update(
                    rmstart=oldstart + i1,
                    rmend=oldstart + i2,
                )
            elif tag == 'insert':
                # b[j1:j2] should be inserted at a[i1:i1].
                # Note that i1 == i2 in this case.
                self._extend_span_update(
                    estart=oldstart + i2,
                    elength=j2 - j1,
                )
        del self._spans['opcodes']

    def strdel(self, start, end):
        """Remove the given range from self.string.

        0 <= start <= end
        
        If an operation includes both insertion and deletion. It's safer to
        use the `strins` function first. Otherwise there is a possibility
        of insertion in the wrong spans.
        """
        lststr = self._lststr
        lststr0 = lststr[0]
        ss = self._get_span()[0]
        end += ss
        start += ss
        # Updating lststr
        lststr[0] = lststr0[:start] + lststr0[end:]
        # Updating spans
        self._shrink_span_update(
            rmstart=start,
            rmend=end,
        )

    def _get_span(self):
        """Return the self-span."""
        return (0, len(self._lststr[0]))

    def _not_in_subspans_split(self, char):
        """Split self.string using `char` unless char is in self._spans."""
        # not used
        ss, se = self._get_span()
        string = self._lststr[0][ss:se]
        splits = []
        findstart = 0
        in_spans = self._in_subspans_factory()
        while True:
            index = string.find(char, findstart)
            while in_spans(ss + index):
                index = string.find(char, index + 1)
            if index == -1:
                return splits + [string[findstart:]]
            splits.append(string[findstart:index])
            findstart = index + 1

    def _not_in_subspans_partition(self, char):
        """Partition self.string using `char` unless char is in self._spans."""
        ss, se = self._get_span()
        string = self._lststr[0][ss:se]
        findstart = 0
        in_spans = self._in_subspans_factory()
        index = string.find(char, findstart)
        while in_spans(ss + index):
            index = string.find(char, index + 1)
        if index == -1:
            return (string, '', '')
        return (string[:index], char, string[index+1:])

    def _not_in_subspans_split_spans(self, char):
        """Like _not_in_subspans_split but return spans."""
        ss, se = self._get_span()
        string = self._lststr[0][ss:se]
        results = []
        findstart = 0
        in_spans = self._in_subspans_factory()
        while True:
            index = string.find(char, findstart)
            while in_spans(ss + index):
                index = string.find(char, index + 1)
            if index == -1:
                return results + [(ss + findstart, se)]
            results.append((ss + findstart, ss + index))
            findstart = index + 1

    def _in_subspans_factory(self):
        """Return a function that can tell if an index is in subspans.

        Checked subspans types are:
        (
            'templates', 'parameters', 'functions',
            'wikilinks', 'comments', 'exttags'
        ).
        """
        # Calculate subspans
        ss, se = self._get_span()
        subspans = []
        for key in (
            'templates', 'parameters', 'functions',
            'wikilinks', 'comments', 'exttags'
        ):
            for span in self._spans[key]:
                if ss < span[0] and span[1] <= se:
                    subspans.append(span)
        # The return function
        def in_spans(index):
            """Return True if the given index is found within a subspans."""
            for span in subspans:
                if span[0] <= index < span[1]:
                    return True
            return False
        return in_spans

    def _gen_subspan_indices(self, type_):
        """Return all the subspan indices including self._get_span()"""
        ss, se = self._get_span()
        for i, s in enumerate(self._spans[type_]):
            # Including self._get_span()
            if ss <= s[0] and s[1] <= se:
                yield i
        

    def _shrink_span_update(self, rmstart, rmend):
        """Update self._spans according to the removed span.

        Warning: If an operation involves both _shrink_span_update and
        _extend_span_update, you might wanna consider doing the
        _extend_span_update before the _shrink_span_update as this function
        can cause data loss in self._spans.
        """
        # Note: No span should be removed from _spans.
        rmlength = rmend - rmstart
        for t, spans in self._spans.items():
            for i, (spanstart, spanend) in enumerate(spans):
                if spanend <= rmstart:
                    continue
                elif rmend <= spanstart:
                    # removed part is before the span
                    spans[i] = (spanstart - rmlength, spanend - rmlength)
                elif rmstart < spanstart:
                    # spanstart needs to be changed
                    # we already know that rmend is after the spanstart
                    # so the new spanstart should be located at rmstart
                    if rmend <= spanend:
                        spans[i] = (rmstart, spanend - rmlength)
                    else:
                        # Shrink to an empty string.
                        spans[i] = (rmstart, rmstart)
                else:
                    # we already know that spanstart is before the rmstart
                    # so the spanstart needs no change.
                    if rmend <= spanend:
                        spans[i] = (spanstart, spanend - rmlength)
                    else:
                        spans[i] = (spanstart, rmstart)

    def _extend_span_update(self, estart, elength):
        """Update self._spans according to the added span."""
        # Note: No span should be removed from _spans.
        ss, se = self._get_span()
        for spans in self._spans.values():
            for i, (spanstart, spanend) in enumerate(spans):
                if estart < spanstart or (
                    # Not at the beginning of selfspan
                    estart == spanstart and spanstart != ss and spanend != se
                ):
                    # Added part is before the span
                    spans[i] = (spanstart + elength, spanend + elength)
                elif spanstart < estart < spanend or (
                    # At the end of selfspan
                    estart == spanstart and spanstart== ss and spanend == se
                ) or (
                    estart == spanend and spanend == se and spanstart == ss
                ):
                    # Added part is inside the span
                    spans[i] = (spanstart, spanend + elength)


    def _get_indent_level(self, with_respect_to=None):
        """Calculate the indent level for self.pprint function.

        Minimum returned value is 1.
        Being part of any Template or Parserfunction increases the indent level
        by one.

        `with_respect_to` is an instance of WikiText object.
        """
        ss, se = self._get_span()
        level = 1 # a template is always found in itself
        if with_respect_to is None:
            for s, e in self._spans['templates']:
                if s < ss and se < e:
                    level += 1
            for s, e in self._spans['functions']:
                if s < ss and se < e:
                    level += 1
            return level
        else:
            rs, re = with_respect_to._get_span()
            for s, e in self._spans['templates']:
                if rs <= s < ss and se < e <= re:
                    level += 1
            for s, e in self._spans['functions']:
                if rs <= s < ss  and se < e <= re:
                    level += 1
            return level

    def _shadow(
        self,
        types=('templates', 'wikilinks', 'functions', 'exttags', 'comments'),
        repl='_',
    ):
        """Return a copy of self.string with specified subspans replaced.

        This function is used in finding the spans of wikitables.
        """
        ss, se = self._get_span()
        shadow = self.string
        for type_ in types:
            for sss, sse in self._spans[type_]:
                if sss < ss or sse > se:
                    continue
                shadow = (
                    shadow[:sss - ss] +
                    (sse - sss) * '_' +
                    shadow[sse - ss:]
                )
        return shadow
