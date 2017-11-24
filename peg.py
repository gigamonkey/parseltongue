#!/usr/bin/env python3

from parseltongue import *

def token(s):
    ws = star(choice(literal(' '), literal('\t')))
    return ws.then(literal(s)).then(ws).returning(1)

def as_text(r):
    return ''.join(x for x in r if x is not None)

def namechar(c):
    return c.isalnum() or c == '_'

def notspace(c):
    return not c.isspace()

def hex(c):
    return c in '0123456789abcdefABCDEF'

def unwrap(seq):
    if len(seq.exprs) == 1:
        return seq.exprs[0]
    else:
        return seq


def token_matcher(text):
    return match(star('ws')).then(literal(text)).then(star('ws')).returning(1)

def make_choice(r):
    return ChoiceMatcher([r[0], *[x[1] for x in r[1]]])

g = {
    'grammar'         : star('production').then(eof).returning(0),
    'production'      : match('name').then(token(':=')).then('sequence').then(star('ws')).then('eol').returning(lambda r: (r[0], unwrap(r[2]))),
    'name'            : plus(namechar).returning(as_text),
    'expression'      : choice('choice', 'star', 'plus', 'optional', 'and', 'not', 'unicode', 'rule', 'parenthesized', 'literal', 'token').then(star('ws')).returning(0),
    'base_expression' : choice('unicode', 'rule', 'parenthesized', 'literal', 'token'),
    'rule'            : match('name').returning(RuleMatcher),
    'parenthesized'   : token('(').then('sequence').then(token(')')).returning(lambda r: unwrap(r[1])),
    'star'            : match('base_expression').then(token('*')).returning(lambda r: StarMatcher(r[0])),
    'plus'            : match('base_expression').then(token('+')).returning(lambda r: PlusMatcher(r[0])),
    'optional'        : match('base_expression').then(token('?')).returning(lambda r: OptionalMatcher(r[0])),
    'sequence'        : star('expression').returning(SequenceMatcher),
    'choice'          : match('base_expression').then(plus(token('|').then('base_expression'))).returning(make_choice),
    'and'             : token('&').then('expression').returning(lambda r: AndMatcher(r[1])),
    'not'             : token('!').then('expression').returning(lambda r: NotMatcher(r[1])),
    'literal'         : literal("'").then(star(not_looking_at(literal("'")).then(lambda _: True).returning(as_text)).returning(as_text)).then(literal("'")).returning(lambda r: StringMatcher(r[1])),
    'token'           : literal('#').then(plus(notspace)).returning(lambda r: token_matcher(as_text(r[1]))),
    'ws'              : choice(literal(' '), literal('\t')),
    'eol'             : literal('\n'),
    'unicode'         : literal('u+').then(plus(hex)).returning(lambda r: StringMatcher(chr(int(as_text(r[1]), 16)))),
}


def grammar(file):
    with open(file) as f:
        input = TextInput(f.read())
        ok, input, r = parse(g, 'grammar', input)
        if ok:
            return dict(r)
        else:
            raise Exception("Can't parse {}".format(file))


if __name__ == '__main__':

    import sys
    import json

    r = grammar(sys.argv[1])
    for a, b in r.items():
        print('{} => {}'.format(a, b))
