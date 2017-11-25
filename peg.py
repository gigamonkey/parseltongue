#!/usr/bin/env python3

from parseltongue import *

def namechar(c):
    return c.isalnum() or c == '_'

def notspace(c):
    return not c.isspace()

def hex(c):
    return c in '0123456789abcdefABCDEF'

def token(text):
    return match(star('ws')).then(literal(text)).then(star('ws')).returning(1)

def make_choice(r):
    return ChoiceMatcher([r[0], *[x[1] for x in r[1]]])

def make_sequence(r):
    return r[0] if len(r) == 1 else SequenceMatcher(r)

def any_char(c):
    return True

g = {
    'grammar'         : star('production').then(eof).returning(0),
    'production'      : star('ignored').then('name').then(token(':=')).then('expression').then(star('ws')).then('eol').then(star('ignored')).returning(lambda r: (r[1], r[3])),
    'name'            : plus(namechar).text(),
    'expression'      : choice('choice', 'sequence'),
    'choice'          : match('sequence').then(plus(token('|').then('sequence'))).returning(make_choice),
    'sequence'        : star(choice('star', 'plus', 'optional', 'and', 'not', 'base_expression').then(star('ws')).returning(0)).returning(make_sequence),
    'base_expression' : choice('regex', 'unicode', 'rule', 'parenthesized', 'literal', 'token'),
    'parenthesized'   : token('(').then('expression').then(token(')')).returning(1),
    'regex'           : literal('/').then(plus(not_looking_at(literal('/')).then(any_char).returning(1)).text(RegexMatcher)).then(literal('/')).returning(1),
    'unicode'         : match(star('ws')).then(literal('u+').then(plus(hex)).returning(lambda r: StringMatcher(chr(int(text(r[1]), 16))))).then(star('ws')).returning(1),
    'rule'            : match('name').returning(RuleMatcher),
    'star'            : match('base_expression').then(token('*')).returning(lambda r: StarMatcher(r[0])),
    'plus'            : match('base_expression').then(token('+')).returning(lambda r: PlusMatcher(r[0])),
    'optional'        : match('base_expression').then(token('?')).returning(lambda r: OptionalMatcher(r[0])),
    'and'             : token('&').then('base_expression').returning(lambda r: AndMatcher(r[1])),
    'not'             : token('!').then('base_expression').returning(lambda r: NotMatcher(r[1])),
    'literal'         : literal("'").then(star(not_looking_at(literal("'")).then(lambda _: True).text()).text()).then(literal("'")).returning(lambda r: StringMatcher(r[1])),
    'token'           : literal('`').then(plus(not_looking_at(literal('`')).then(notspace).returning(1))).then(literal('`')).returning(1).text(token),
    'ws'              : choice(literal(' '), literal('\t')),
    'eol'             : literal('\n'),
    'blankline'       : star('ws').then('eol'),
    'comment'         : star('ws').then(literal('#')).then(star(not_looking_at('eol').then(any_char))).then('eol'),
    'ignored'         : choice('blankline', 'comment'),
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

    import parseltongue

    parseltongue.verbose = False

    r = grammar(sys.argv[1])
    for a, b in r.items():
        print('{} => {}'.format(a, b))
