from __future__ import annotations

from pytest import mark

from wikitextparser import parse


def parse_names(text: str) -> list[str]:
    """Extract all parsed ref names from a piece of wikitext."""
    return [
        tag.attrs['name']
        for tag in parse(text).get_tags()
        if 'name' in tag.attrs
    ]


REFERENCE_CASES = [
    (
        'asd',
        [
            '<ref name="asd">text</ref>',
            '<ref name="asd" />',
            '<ref name="asd"/>',
            '<ref name=asd />',
            '<ref name=asd/>',
            '<ref name="asd />',
            '<ref name="asd/>',
        ],
    ),
    (
        "as'd",
        [
            '<ref name="as\'d">text</ref>',
            '<ref name="as\'d" />',
            '<ref name="as\'d"/>',
            "<ref name=as'd />",
            "<ref name=as'd/>",
            '<ref name="as\'d />',
            '<ref name="as\'d/>',
        ],
    ),
    (
        'as"d',
        [
            "<ref name='as\"d'>text</ref>",
            "<ref name='as\"d' />",
            "<ref name='as\"d'/>",
            '<ref name=as"d />',
            '<ref name=as"d/>',
            '<ref name=\'as"d />',
            '<ref name=\'as"d/>',
        ],
    ),
    (
        '<asd',
        [
            '<ref name="<asd">text</ref>',
            '<ref name="<asd" />',
            '<ref name="<asd"/>',
            "<ref name='<asd' />",
            "<ref name='<asd'/>",
            '<ref name="<asd />',
            '<ref name="<asd/>',
            "<ref name='<asd />",
            "<ref name='<asd/>",
            '<ref name=<asd />',
            '<ref name=<asd/>',
        ],
    ),
    (
        'asd/',
        [
            '<ref name="asd/">text</ref>',
            '<ref name="asd/" />',
            '<ref name="asd/"/>',
            '<ref name="asd/ />',
            '<ref name="asd//>',
            '<ref name=asd/ />',
            '<ref name=asd//>',
        ],
    ),
    (
        'ax=sd',
        [
            '<ref name="ax=sd">text</ref>',
            '<ref name="ax=sd" />',
            '<ref name=ax=sd />',
        ],
    ),
]


@mark.parametrize('expected_name,variants', REFERENCE_CASES)
def test_each_variant_parses_to_expected_name(expected_name, variants):
    """
    Every syntactic form of the same reference name should
    normalize to the same parsed name.
    """
    for variant in variants:
        names = parse_names(variant)

        assert len(names) == 1, (
            f'Expected exactly one ref name from:\n{variant}\nGot: {names}'
        )

        assert names[0] == expected_name


@mark.parametrize('expected_name,variants', REFERENCE_CASES)
def test_all_variants_are_consistent(expected_name, variants):
    """
    Parse all variants together and verify that every one
    produces the same normalized name.
    """
    text = '\n'.join(variants)

    names = parse_names(text)

    assert len(names) == len(variants)

    assert names == [expected_name] * len(variants)


def test_mixed_reference_names_remain_distinct():
    """
    Different reference names should not collapse into each other.
    """
    text = """
    <ref name="asd">text</ref>
    <ref name="as'd">text</ref>
    <ref name='as"d'>text</ref>
    <ref name="<asd">text</ref>
    <ref name="asd/">text</ref>
    <ref name="ax=sd">text</ref>
    """

    assert parse_names(text) == [
        'asd',
        "as'd",
        'as"d',
        '<asd',
        'asd/',
        'ax=sd',
    ]
