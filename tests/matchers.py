#!/usr/bin/env python3

from parseltongue import *

def test_matcher(matcher, should_match, should_not_match):
    g = { 'rule': matcher.text() }
    for x in should_match:
        ok, _, r = parse(g, 'rule', TextInput(x))
        print('{} should parse ... {}'.format(x, 'ok' if ok else 'FAIL'))
    for x in should_not_match:
        ok, _, r = parse(g, 'rule', TextInput(x))
        print('{} should not parse ... {}'.format(x, 'ok' if not ok else 'FAIL'))


if __name__ == '__main__':

    test_matcher(RegexMatcher('[ab]+'), ['a', 'b', 'ab', 'aaabbb'], ['', 'ca', 'def'])
