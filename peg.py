#!/usr/bin/env python3

from parseltongue import *


def token(s):
    ws = star(choice(literal(' '), literal('\t')))
    return ws.then(literal(s)).then(ws).returning(1)

def as_text(r):
    return ''.join(x for x in r if x is not None)

def namechar(c):
    return c.isalnum() or c == '_'

def unwrap(seq):
    if len(seq.exprs) == 1:
        return seq.exprs[0]
    else:
        return seq

def make_choice(r):
    return ChoiceMatcher([r[0], *[x[1] for x in r[1]]])


g = {
    'grammar'         : star('production').then(eof).returning(0),
    'production'      : match('name').then(token(':=')).then('sequence').then(star('ws')).then('eol').returning(lambda r: (r[0], unwrap(r[2]))),
    'name'            : plus(namechar).returning(as_text),
    'expression'      : choice('choice', 'star', 'plus', 'optional', 'and', 'not', 'rule', 'parenthesized', 'literal').then(star('ws')).returning(0),
    'base_expression' : choice('rule', 'parenthesized', 'literal'),
    'rule'            : match('name').returning(RuleMatcher),
    'parenthesized'   : token('(').then('sequence').then(token(')')).returning(1),
    'star'            : match('base_expression').then(token('*')).returning(lambda r: StarMatcher(r[0])),
    'plus'            : match('base_expression').then(token('+')).returning(lambda r: PlusMatcher(r[0])),
    'optional'        : match('base_expression').then(token('?')).returning(lambda r: OptionalMatcher(r[0])),
    'sequence'        : star('expression').returning(SequenceMatcher),
    'choice'          : match('base_expression').then(plus(token('|').then('base_expression'))).returning(make_choice),
    'and'             : token('&').then('expression').returning(lambda r: AndMatcher(r[1])),
    'not'             : token('!').then('expression').returning(lambda r: NotMatcher(r[1])),
    'literal'         : literal("'").then(star(not_looking_at(literal("'")).then(lambda _: True).returning(as_text)).returning(as_text)).then(literal("'")).returning(lambda r: StringMatcher(r[1])),
    'ws'              : choice(literal(' '), literal('\t')),
    'eol'             : literal('\n'),
}


if __name__ == '__main__':

    import sys
    import json

    with open(sys.argv[1]) as f:
        input = TextInput(f.read())
        ok, input, r = parse(g, 'grammar', input)
        if ok:
            for a, b in r:
                print('{} => {}'.format(a, b))
        else:
            print('Parse failed')