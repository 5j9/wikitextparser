from pytest import mark

from wikitextparser import Template


def test_rm_dup_args_safe():
    # Don't remove duplicate positional args in different positions
    s = '{{cite|{{t1}}|{{t1}}}}'
    t = Template(s)
    t.rm_dup_args_safe()
    assert s == t.string
    # Don't remove duplicate args if the have different values
    s = '{{template|year=9999|year=2000}}'
    t = Template(s)
    t.rm_dup_args_safe()
    assert s == t.string
    # Detect positional and keyword duplicates
    t = Template('{{t|1=|}}')
    t.rm_dup_args_safe()
    assert '{{t|}}' == t.string
    # Detect same-name same-value.
    # It's OK to ignore whitespace in positional arguments.
    t = Template('{{t|n=v|  n=v  }}')
    t.rm_dup_args_safe()
    assert '{{t|  n=v  }}' == t.string
    # It's not OK to ignore whitespace in positional arguments.
    t = Template('{{t| v |1=v}}')
    t.rm_dup_args_safe()
    assert '{{t| v |1=v}}' == t.string
    # Removing a positional argument affects the name of later ones.
    t = Template('{{t|1=|||}}')
    t.rm_dup_args_safe()
    assert '{{t|||}}' == t.string
    # Triple duplicates
    t = Template('{{t|1=v|v|1=v}}')
    t.rm_dup_args_safe()
    assert '{{t|1=v}}' == t.string
    # If the last duplicate has a defferent value, still remove of the
    # first two
    t = Template('{{t|1=v|v|1=u}}')
    t.rm_dup_args_safe()
    assert '{{t|v|1=u}}' == t.string
    # tag
    # Remove safe duplicates even if tag option is activated
    t = Template('{{t|1=v|v|1=v}}')
    t.rm_dup_args_safe(tag='<!-- dup -->')
    assert '{{t|1=v}}' == t.string
    # Tag even if one of the duplicate values is different.
    t = Template('{{t|1=v|v|1=u}}')
    t.rm_dup_args_safe(tag='<!-- dup -->')
    assert '{{t|v<!-- dup -->|1=u}}' == t.string
    # Duplicate argument's value is empty
    t = Template('{{t|b|1=c|1=}}')
    t.rm_dup_args_safe()
    assert '{{t|b|1=c}}' == t.string


def test_rm_dup_args_safe_cached_arguments():
    t = Template('{{t|a=1|a=1|b=2}}')

    # Populate the arguments cache before mutating through the method.
    arguments = t.arguments
    assert len(arguments) == 3

    t.rm_dup_args_safe()

    assert '{{t|a=1|b=2}}' == t.string
    assert [arg.string for arg in t.arguments] == ['|a=1', '|b=2']


def test_rm_dup_args_safe_after_argument_mutation():
    t = Template('{{t|a=1|a=2}}')

    # Populate the cache, then mutate through an Argument.
    arguments = t.arguments
    arguments[1].value = '1'

    t.rm_dup_args_safe()

    assert '{{t|a=1}}' == t.string
    assert len(t.arguments) == 1


def test_rm_dup_args_safe_idempotent():
    t = Template('{{t|a=1|a=1|b=2|b=}}')

    t.rm_dup_args_safe()
    first_result = t.string

    t.rm_dup_args_safe()

    assert first_result == '{{t|a=1|b=2}}'
    assert first_result == t.string


@mark.skip('tracked as issue #151')
def test_rm_dup_args_safe_multiple_values_and_empty():
    t = Template('{{t|a=1|a=|a=2|a=1|a=}}')

    t.rm_dup_args_safe()

    assert '{{t|a=2|a=1}}' == t.string


def test_rm_dup_args_safe_multiple_duplicate_groups_with_tag():
    t = Template('{{t|a=1|a=2|a=1|b=3|b=4|b=3}}')

    t.rm_dup_args_safe(tag='<!-- dup -->')

    assert '{{t|a=2<!-- dup -->|a=1|b=4<!-- dup -->|b=3}}' == t.string


def test_arguments_cache_is_invalidated_by_rm_dup_args_safe():
    t = Template('{{t|a=1|a=1}}')

    arguments = t.arguments
    assert t.arguments is arguments
    assert len(arguments) == 2

    t.rm_dup_args_safe()

    new_arguments = t.arguments
    assert new_arguments is not arguments
    assert len(new_arguments) == 1
    assert new_arguments[0].string == '|a=1'


def test_rm_dup_args_safe_whitespace_only_positional_value():
    t = Template('{{t|a=1|   |1=1}}')

    t.rm_dup_args_safe()

    # The positional "   " is not an empty value.
    assert '{{t|a=1|   |1=1}}' == t.string
